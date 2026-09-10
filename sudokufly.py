"""Level 1: visual cue conditioning inside the full MaleCNS connectome.

No external trained policy. See README.md for setup and the experiment protocol.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT / ".upstream" / "stonkfly"
UPSTREAM_COMMIT = "78ef3e05ab0fa086032098558d893667068944a0"
CUES = ("vertical", "horizontal")


def cue_frame(cue):
    """Two centered, symmetric patterns with exactly equal pixel histograms."""
    frame = np.full((180, 320, 3), 235, dtype=np.uint8)
    if cue == "vertical":
        for x in (116, 154, 192):
            frame[42:138, x : x + 12] = 24
    elif cue == "horizontal":
        for y in (46, 84, 122):
            frame[y : y + 12, 112:208] = 24
    elif cue != "blank":
        raise ValueError(f"Unknown cue: {cue}")
    return frame


def memory_state(brain):
    fraction = brain.weight[brain.circuit["edges"]] / brain.baseline_plastic
    return {
        **brain.memory(),
        "maximum_efficacy": float(fraction.max()),
        "at_lower_bound": int(np.count_nonzero(fraction <= 0.100001)),
        "at_upper_bound": int(np.count_nonzero(fraction >= 1.999999)),
        "u_min": float(brain.memory_u.min()),
        "u_max": float(brain.memory_u.max()),
        "u_sha256": hashlib.sha256(brain.memory_u.tobytes()).hexdigest(),
        "w_sha256": hashlib.sha256(brain.memory_w.tobytes()).hexdigest(),
    }


def run_trial(brain, frame, cue, target, motors, args, *, learn, feedback=None):
    """The action is committed from spikes before the target can deliver feedback.

    feedback='outcome' uses correctness; reward/aversive replay a yoked pulse.
    feedback=None disables external reinforcement (evaluation).
    Electrical/eligibility state resets between trials; synaptic memory survives.
    """
    brain.reset(keep_memory=True)
    brain.weights_frozen = not learn
    before = memory_state(brain)
    started = time.perf_counter()
    counts, _ = brain.rgb_step(frame, args.observe_ms, learning=learn)
    seconds = args.observe_ms / 1000
    left_hz = float(counts[motors["left"]].mean() / seconds)
    right_hz = float(counts[motors["right"]].mean() / seconds)
    difference = right_hz - left_hz
    action = (
        "accept" if difference >= args.threshold_hz else
        "reject" if difference <= -args.threshold_hz else "timeout"
    )
    # Only the environment evaluates this label, after the action is fixed.
    correct = action == target
    delivered = (
        ("reward" if correct else "aversive")
        if feedback == "outcome" else feedback
    )
    kc_counts = counts[brain.circuit["kc"]]
    row = {
        "cue": cue,
        "target": target,
        "action": action,
        "correct": correct,
        "left_hz": left_hz,
        "right_hz": right_hz,
        "difference_hz": difference,
        "observation_KC_spikes": int(kc_counts.sum()),
        "observation_active_KCs": int(np.count_nonzero(kc_counts)),
        "observation_KC_sha256": hashlib.sha256(kc_counts.tobytes()).hexdigest(),
        "observation_spikes": int(counts.sum()),
        "observation_spikes_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
        "observation_reward_spikes": int(counts[brain.circuit["reward"]].sum()),
        "observation_aversive_spikes": int(counts[brain.circuit["aversive"]].sum()),
        "feedback": delivered,
        "feedback_ms": args.feedback_ms if delivered else 0,
        "learning_enabled": learn,
        "memory_before": before,
    }
    if delivered:
        reinforced, _ = brain.rgb_step(
            frame, args.feedback_ms, learning=learn,
            stimulation=(brain.circuit[delivered], args.pulse_current),
        )
        row["feedback_target_spikes"] = int(
            reinforced[brain.circuit[delivered]].sum()
        )
        brain.rgb_step(cue_frame("blank"), args.settle_ms, learning=learn)
    row["memory_after"] = memory_state(brain)
    row["wall_seconds"] = time.perf_counter() - started
    if not learn and row["memory_after"] != before:
        raise RuntimeError("Frozen trial changed synaptic memory")
    return row


def score(rows):
    """Timeouts count as errors; repeated deterministic trials are not subjects."""
    responded = [row for row in rows if row["action"] != "timeout"]
    by_cue = {
        cue: sum(r["correct"] for r in rows if r["cue"] == cue)
        / sum(r["cue"] == cue for r in rows)
        for cue in CUES
    }
    return {
        "trials": len(rows),
        "correct": sum(row["correct"] for row in rows),
        "accuracy": sum(row["correct"] for row in rows) / len(rows),
        "balanced_accuracy": sum(by_cue.values()) / len(CUES),
        "by_cue": by_cue,
        "coverage": len(responded) / len(rows),
        "timeouts": len(rows) - len(responded),
        "accuracy_when_responding": (
            sum(row["correct"] for row in responded) / len(responded)
            if responded else None
        ),
    }


def evaluate(brain, frames, targets, motors, args, record, phase):
    rows = []
    for cue in CUES * 2:
        row = run_trial(
            brain, frames[cue], cue, targets[cue], motors, args,
            learn=False, feedback=None,
        )
        record(phase, row)
        rows.append(row)
    for first, repeated in zip(rows[:2], rows[2:]):
        if first["observation_spikes_sha256"] != repeated["observation_spikes_sha256"]:
            raise RuntimeError("Identical reset-state evaluations were not repeatable")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "runs" / time.strftime("level-01-%Y%m%d-%H%M%S"))
    parser.add_argument("--trials", type=int, default=8, help="Balanced training trials per arm and target mapping")
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument("--observe-ms", type=float, default=500)
    parser.add_argument("--feedback-ms", type=float, default=200)
    parser.add_argument("--settle-ms", type=float, default=250)
    parser.add_argument("--threshold-hz", type=float, default=2)
    parser.add_argument("--pulse-current", type=float, default=20)
    parser.add_argument("--eta", type=float, default=0.001)
    parser.add_argument("--probe", action="store_true", help="Only run untrained cue/feedback diagnostics")
    args = parser.parse_args()
    if args.trials < 2 or args.trials % 2:
        parser.error("--trials must be a positive even number of at least 2")
    for key in ("observe_ms", "feedback_ms", "settle_ms", "threshold_hz", "pulse_current", "eta"):
        value = getattr(args, key)
        if not np.isfinite(value) or value <= 0:
            parser.error(f"{key} must be finite and positive")
    for key in ("observe_ms", "feedback_ms", "settle_ms"):
        ticks = getattr(args, key) / 0.1
        if ticks < 1 or abs(ticks - round(ticks)) > 1e-6:
            parser.error(f"{key} must be a positive multiple of 0.1 ms")
    if not UPSTREAM.is_dir():
        parser.error("Pinned upstream is missing; follow README.md setup")
    commit = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True,
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"], text=True,
    ).strip()
    if commit != UPSTREAM_COMMIT or dirty:
        parser.error("Upstream must be the clean, pinned Stonkfly commit")
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    os.environ["STONKFLY_DATA"] = str(ROOT / "data")
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.common import annotations
    from stonkfly.neural.sensory import retinal_samples
    from stonkfly.neural.visual import VisualMemoryBrain

    print("Verifying connectome and loading the full neural model...", flush=True)
    verified = verify()
    started = time.perf_counter()
    brain = VisualMemoryBrain(eta=args.eta)
    initial_weights = brain.weight.copy()
    a = annotations(brain.ids)
    motors = {
        side: np.flatnonzero(a.type.eq("DNp20") & a.somaSide.eq(letter))
        for side, letter in (("left", "L"), ("right", "R"))
    }
    if any(len(indices) == 0 for indices in motors.values()):
        raise RuntimeError("Missing fixed DNp20 decoder cells")
    frames = {cue: cue_frame(cue) for cue in CUES}
    if not np.array_equal(
        np.bincount(frames[CUES[0]].ravel(), minlength=256),
        np.bincount(frames[CUES[1]].ravel(), minlength=256),
    ):
        raise RuntimeError("Cue brightness histograms differ")
    sensory = {}
    for cue, frame in frames.items():
        Image.fromarray(frame).save(args.out / f"cue-{cue}.png")
        light = retinal_samples(frame, brain.uv)
        sensory[cue] = {
            "RGB_sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
            "RGB_mean": float(frame.mean()),
            "retinal_mean": float(light.mean()),
            "retinal_min": float(light.min()),
            "retinal_max": float(light.max()),
            "retinal_sha256": hashlib.sha256(light.tobytes()).hexdigest(),
        }
    protocol = {
        "level": 1,
        "task": "Counterbalanced visual cue accept/reject conditioning",
        "mode": "probe" if args.probe else "controlled_pilot",
        "parameters": {k: v for k, v in vars(args).items() if k != "out"},
        "upstream_repository": "https://github.com/nftechie/stonkfly",
        "upstream_commit": commit,
        "experiment_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "dependencies": {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "pyarrow", "Pillow")},
        "python": platform.python_version(),
        "platform": platform.platform(),
        "data": verified,
        "brain_configuration": brain.configuration_signature(),
        "kernel": brain.build,
        "circuit": brain.circuit["report"],
        "visual": brain.visual_report,
        "sensory": sensory,
        "decoder": {
            "rule": "Mean DNp20 right minus left Hz; >=threshold accept, <=-threshold reject, otherwise timeout. No DNpe017 gating.",
            "cell_ids": {k: [int(brain.ids[i]) for i in v] for k, v in motors.items()},
            "trained": False,
        },
        "reset": "Reset electrical states, queues, adaptation and KC/DAN traces between trials; preserve u/w and plastic weights during an arm.",
        "evaluation": "weights_frozen=True; no teaching pulses; each cue repeated from identical reset state. Repeats are determinism checks, not independent samples.",
        "controls": "Same cue schedule for learned/frozen/shuffled; frozen receives learned-arm pulses; shuffled receives a seeded permutation of those exact pulses; erase weights and u/w after learned evaluation.",
        "progression_criterion": "Both opposite mappings: post balanced accuracy >=0.75, gain over initial >=0.25, gain over frozen and shuffled >=0.25; distinct shuffled pulse sequence; exact frozen and erased baseline recovery. An exploratory gate, not statistical validation.",
        "claim_boundary": "Two artificial cues; no Sudoku reasoning, biological replication, or connectome advantage established.",
    }
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"loaded_seconds": time.perf_counter() - started, "neurons": brain.n, "plastic_edges": len(brain.circuit["edges"])}), flush=True)
    results = []
    with (args.out / "trials.jsonl").open("x") as log:
        for mapping in range(1 if args.probe else 2):
            targets = {
                cue: "accept" if index == mapping else "reject"
                for index, cue in enumerate(CUES)
            }

            def record(phase, row):
                row.update(mapping=mapping, phase=phase)
                log.write(json.dumps(row, allow_nan=False) + "\n")
                log.flush()
                print(json.dumps({
                    "mapping": mapping, "phase": phase, "cue": row["cue"],
                    "action": row["action"], "correct": row["correct"],
                    "KC_spikes": row["observation_KC_spikes"],
                    "changed_edges": row["memory_after"]["changed_edges"],
                    "seconds": round(row["wall_seconds"], 3),
                }), flush=True)

            brain.reset(keep_memory=False)
            baseline = evaluate(brain, frames, targets, motors, args, record, "baseline")
            if args.probe:
                for kind in ("reward", "aversive"):
                    row = run_trial(
                        brain, frames[CUES[0]], CUES[0], targets[CUES[0]], motors,
                        args, learn=False, feedback=kind,
                    )
                    record(f"probe_{kind}", row)
                results.append({"mapping": mapping, "baseline": score(baseline)})
                break

            order = list(CUES) * (args.trials // 2)
            random.Random(args.seed + mapping).shuffle(order)
            result = {"mapping": mapping, "targets": targets, "cue_order": order, "baseline": score(baseline)}
            learned_pulses = []
            shuffled_pulses = []
            for arm in ("learned", "frozen", "shuffled"):
                brain.reset(keep_memory=False)
                for index, cue in enumerate(order):
                    feedback = (
                        "outcome" if arm == "learned" else
                        learned_pulses[index] if arm == "frozen" else shuffled_pulses[index]
                    )
                    row = run_trial(
                        brain, frames[cue], cue, targets[cue], motors, args,
                        learn=arm != "frozen", feedback=feedback,
                    )
                    record(f"{arm}_train", row)
                    if arm == "learned":
                        learned_pulses.append(row["feedback"])
                trained_memory = memory_state(brain)
                np.savez_compressed(
                    args.out / f"mapping-{mapping}-{arm}-memory.npz",
                    edge_indices=brain.circuit["edges"],
                    weights=brain.weight[brain.circuit["edges"]],
                    u=brain.memory_u, w=brain.memory_w,
                )
                after = evaluate(brain, frames, targets, motors, args, record, f"{arm}_eval")
                # The large graph is used intact; no other edge may be trained.
                changed = np.flatnonzero(brain.weight != initial_weights)
                if np.setdiff1d(changed, brain.circuit["edges"]).size:
                    raise RuntimeError("Connections outside the declared memory circuit changed")
                result[arm] = {
                    "evaluation": score(after), "memory": trained_memory,
                    "nonplastic_weights_unchanged": True,
                    "output_changed_from_baseline": any(
                        r["difference_hz"] != b["difference_hz"]
                        for r, b in zip(after, baseline)
                    ),
                }
                if arm == "learned":
                    shuffled_pulses = learned_pulses.copy()
                    random.Random(args.seed + mapping + 10000).shuffle(shuffled_pulses)
                    result["learned_pulses"] = learned_pulses
                    result["shuffled_pulses"] = shuffled_pulses
                    result["shuffle_is_distinct"] = shuffled_pulses != learned_pulses
                    brain.reset(keep_memory=False)
                    erased = evaluate(brain, frames, targets, motors, args, record, "erased_eval")
                    result["erased"] = score(erased)
                    result["erasure_recovers_baseline"] = all(
                        r["observation_spikes_sha256"] == b["observation_spikes_sha256"]
                        for r, b in zip(erased, baseline)
                    )
                    if not result["erasure_recovers_baseline"]:
                        raise RuntimeError("Memory erasure failed to recover baseline")
                if arm == "frozen":
                    result["frozen_recovers_baseline"] = all(
                        r["observation_spikes_sha256"] == b["observation_spikes_sha256"]
                        for r, b in zip(after, baseline)
                    )
                    if not result["frozen_recovers_baseline"]:
                        raise RuntimeError("Frozen arm failed to recover baseline")
            learned = result["learned"]["evaluation"]["balanced_accuracy"]
            result["behavior_gate_passed"] = (
                learned >= 0.75
                and learned - result["baseline"]["balanced_accuracy"] >= 0.25
                and all(learned - result[arm]["evaluation"]["balanced_accuracy"] >= 0.25 for arm in ("frozen", "shuffled"))
                and result["shuffle_is_distinct"]
                and result["erasure_recovers_baseline"]
                and result["frozen_recovers_baseline"]
            )
            results.append(result)
            (args.out / "partial-results.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
    summary = {
        "level": 1,
        "status": "probe_complete" if args.probe else "pilot_complete",
        "behavior_gate_passed": None if args.probe else all(r["behavior_gate_passed"] for r in results),
        "learning_demonstrated": False,
        "interpretation": "Pilot only. Progression requires both counterbalanced mappings to improve; repeated deterministic observations are not independent evidence.",
        "elapsed_seconds_including_model_load": time.perf_counter() - started,
        "runs": results,
        "files_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(args.out.iterdir()) if path.is_file()
        },
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"out": str(args.out), "status": summary["status"], "behavior_gate_passed": summary["behavior_gate_passed"]}), flush=True)


if __name__ == "__main__":
    main()
