"""Causal diagnostics for Level 1; preserves the original experiment runner."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from sudokufly import ROOT, UPSTREAM, CUES, cue_frame, expanded_memory_circuit


def measure(brain, frame, duration, motors, *, learn=False, stimulus=None):
    """Observe actual 10-ms simulator bins without changing its timestep."""
    brain.weights_frozen = not learn
    edges = brain.circuit["edges"]
    previous = brain.weight[edges].copy()
    total = np.zeros(brain.n, dtype=np.int32)
    bins = []
    for _ in range(round(duration / 10)):
        counts, _ = brain.rgb_step(frame, 10, learning=learn, stimulation=stimulus)
        total += counts
        bins.append({
            "KC": int(counts[brain.circuit["kc"]].sum()),
            "PAM": int(counts[brain.circuit["reward"]].sum()),
            "PPL": int(counts[brain.circuit["aversive"]].sum()),
            "left": int(counts[motors["left"]].sum()),
            "right": int(counts[motors["right"]].sum()),
            "weight_L1_from_phase_start": float(np.abs(brain.weight[edges] - previous).sum()),
        })
    kc = total[brain.circuit["kc"]]
    left = float(total[motors["left"]].mean() * 1000 / duration)
    right = float(total[motors["right"]].mean() * 1000 / duration)
    delta = brain.weight[edges] - previous
    row = {
        "duration_ms": duration, "learning": learn,
        "KC_spikes": int(kc.sum()), "active_KCs": int(np.count_nonzero(kc)),
        "KC_ids_counts": [[int(brain.ids[i]), int(total[i])] for i in brain.circuit["kc"] if total[i]],
        "PAM_spikes": int(total[brain.circuit["reward"]].sum()),
        "PPL_spikes": int(total[brain.circuit["aversive"]].sum()),
        "left_hz": left, "right_hz": right, "difference_hz": right - left,
        "action": "accept" if right - left >= 2 else "reject" if right - left <= -2 else "timeout",
        "spikes_sha256": hashlib.sha256(total.tobytes()).hexdigest(),
        "changed_edges_in_phase": int(np.count_nonzero(delta)),
        "weight_L1_change": float(np.abs(delta).sum()),
        "weight_signed_change": float(delta.sum()),
        "total_changed_edges": int(np.count_nonzero(brain.weight[edges] != brain.baseline_plastic)),
        "bins": bins,
    }
    if not learn and np.any(delta):
        raise RuntimeError("Frozen diagnostic changed weights")
    return row


def restore_memory(brain, path=None, erase=None):
    """Restore only a committed memory state; all electrical state starts fresh."""
    brain.reset(keep_memory=False)
    if path:
        with np.load(path) as saved:
            if not np.array_equal(saved["edge_indices"], brain.circuit["edges"]):
                raise RuntimeError("Snapshot circuit mismatch")
            brain.weight[brain.circuit["edges"]] = saved["weights"]
            brain.memory_u[:] = saved["u"]
            brain.memory_w[:] = saved["w"]
    if erase is not None:
        brain.weight[brain.circuit["edges"][erase]] = brain.baseline_plastic[erase]
        brain.memory_u[erase] = 0
        brain.memory_w[erase] = 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=("phases", "snapshots", "training", "transition"))
    parser.add_argument("--out", type=Path, default=ROOT / "experiments/level-01/003-diagnosis")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / f"{args.suite}.json"
    if target.exists():
        parser.error(f"Existing result: {target}")
    os.environ["STONKFLY_DATA"] = str(ROOT / "data")
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.common import annotations
    from stonkfly.neural.visual import VisualMemoryBrain

    verified = verify()
    started = time.perf_counter()
    rows = []
    provenance = {
        "suite": args.suite, "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256((ROOT / "sudokufly.py").read_bytes()).hexdigest(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "upstream_head": subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip(),
        "verified_graph": verified,
        "interpretation": "Post-hoc diagnostic interventions, not independent confirmation or a changed progression gate.",
    }
    with (args.out / f"{args.suite}-progress.jsonl").open("x") as log:
        def record(row):
            rows.append(row)
            log.write(json.dumps(row, allow_nan=False) + "\n")
            log.flush()
            print(json.dumps({k: v for k, v in row.items() if k not in ("bins", "KC_ids_counts")}), flush=True)

        for scope in ("baseline", "expanded") if args.suite == "phases" else ("expanded",):
            brain = VisualMemoryBrain(circuit=expanded_memory_circuit() if scope == "expanded" else None)
            a = annotations(brain.ids)
            motors = {side: np.flatnonzero(a.type.eq("DNp20") & a.somaSide.eq(letter))
                      for side, letter in (("left", "L"), ("right", "R"))}
            frames = {cue: cue_frame(cue) for cue in CUES}
            if args.suite == "phases":
                for cue in CUES:
                    for pulse in ("none", "reward", "aversive"):
                        restore_memory(brain)
                        for phase, frame, duration, stimulus in (
                            ("observation", frames[cue], 500, None),
                            ("feedback", frames[cue], 200, None if pulse == "none" else (brain.circuit[pulse], 20)),
                            ("settle", cue_frame("blank"), 250, None),
                        ):
                            row = measure(brain, frame, duration, motors, learn=True, stimulus=stimulus)
                            record({"scope": scope, "cue": cue, "pulse": pulse, "phase": phase, **row})
            elif args.suite == "transition":
                # Matched prehistory isolates cue offset from elapsed time, and
                # full weight freezing tests whether the burst needs plasticity.
                for cue in CUES:
                    for plasticity in ("normal", "frozen"):
                        for interval in ("blank", "continue_cue"):
                            restore_memory(brain)
                            for phase, frame, duration in (
                                ("observation", frames[cue], 500),
                                ("feedback_without_pulse", frames[cue], 200),
                                ("settle", cue_frame("blank") if interval == "blank" else frames[cue], 250),
                            ):
                                row = measure(brain, frame, duration, motors, learn=plasticity == "normal")
                                record({"cue": cue, "plasticity": plasticity, "interval": interval,
                                        "phase": phase, **row})
            elif args.suite == "snapshots":
                saved_root = ROOT / "experiments/level-01/002-expanded-memory"
                profiles = {
                    "untrained": None,
                    "learned_map0": saved_root / "mapping-0-learned-memory.npz",
                    "learned_map1": saved_root / "mapping-1-learned-memory.npz",
                    "shuffled_map1": saved_root / "mapping-1-shuffled-memory.npz",
                }
                for profile, path in profiles.items():
                    for variant in ("nominal", "shift_x_1", "shift_y_4", "blank"):
                        for cue in ("blank",) if variant == "blank" else CUES:
                            restore_memory(brain, path)
                            frame = cue_frame(cue)
                            if variant == "shift_x_1":
                                frame = np.roll(frame, 1, axis=1)
                            if variant == "shift_y_4":
                                frame = np.roll(frame, 4, axis=0)
                            row = measure(brain, frame, 500, motors)
                            record({"profile": profile, "variant": variant, "cue": cue, **row})
                    for cue in CUES:
                        restore_memory(brain, path)
                        measure(brain, cue_frame("blank"), 500, motors)
                        row = measure(brain, frames[cue], 500, motors)
                        record({"profile": profile, "variant": "white_warmup_500ms", "cue": cue, **row})
                post = brain.post[brain.circuit["edges"]]
                types = a.type.fillna("")
                weak = [int(x["index"]) for x in brain.circuit["report"]["memory_outputs"] if x["DAN_contacts"] <= 2]
                ablations = {
                    "restore_MBON05": np.isin(post, np.flatnonzero(types.eq("MBON05"))),
                    "restore_MBON11": np.isin(post, np.flatnonzero(types.eq("MBON11"))),
                    "restore_MBON03": np.isin(post, np.flatnonzero(types.eq("MBON03"))),
                    "restore_weak_DAN_support": np.isin(post, weak),
                    "restore_baseline_targets": np.isin(post, np.flatnonzero(types.isin(("MBON07", "MBON11")))),
                    "restore_added_targets": ~np.isin(post, np.flatnonzero(types.isin(("MBON07", "MBON11")))),
                }
                for name, erase in ablations.items():
                    for cue in CUES:
                        restore_memory(brain, profiles["learned_map1"], erase)
                        row = measure(brain, frames[cue], 500, motors)
                        record({"profile": "learned_map1", "variant": name, "cue": cue,
                                "restored_edges": int(erase.sum()), **row})
            else:
                original = json.loads((ROOT / "experiments/level-01/002-expanded-memory/summary.json").read_text())
                # Cross BOTH label maps with BOTH original training orders, which
                # were confounded with labels in the first two pilot experiments.
                for order_id, run in enumerate(original["runs"]):
                    for mapping in (0, 1):
                        targets = {cue: "accept" if i == mapping else "reject" for i, cue in enumerate(CUES)}
                        for condition in ("normal", "no_external_feedback", "freeze_settle"):
                            restore_memory(brain)
                            for trial, cue in enumerate(run["cue_order"]):
                                brain.reset(keep_memory=True)
                                obs = measure(brain, frames[cue], 500, motors, learn=True)
                                pulse = "reward" if obs["action"] == targets[cue] else "aversive"
                                stim = None if condition == "no_external_feedback" else (brain.circuit[pulse], 20)
                                measure(brain, frames[cue], 200, motors, learn=True, stimulus=stim)
                                measure(brain, cue_frame("blank"), 250, motors, learn=condition != "freeze_settle")
                                record({"order": order_id, "mapping": mapping, "condition": condition,
                                        "phase": "train", "trial": trial, "cue": cue,
                                        "action": obs["action"], "correct": obs["action"] == targets[cue],
                                        "pulse": None if stim is None else pulse})
                            for cue in CUES:
                                brain.reset(keep_memory=True)
                                row = measure(brain, frames[cue], 500, motors)
                                record({"order": order_id, "mapping": mapping, "condition": condition,
                                        "phase": "eval", "cue": cue, "target": targets[cue],
                                        "correct": row["action"] == targets[cue], **row})
            del brain
    output = {"provenance": provenance, "elapsed_seconds": time.perf_counter() - started, "rows": rows}
    target.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"complete": str(target), "seconds": output["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
