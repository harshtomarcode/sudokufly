"""Direct KC conditioning inside the full graph; this does not pass visual Level 1."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np

from sudokufly import ROOT, UPSTREAM, UPSTREAM_COMMIT


def select_cues(brain, annotation):
    """Choose balanced, disjoint ensembles using anatomical contacts only."""
    c = brain.circuit
    contacts = np.rint(brain.baseline_plastic / 0.275).astype(np.int64)
    target_types = annotation.type.iloc[brain.post[c["edges"]]].to_numpy()
    mass = {}
    for name in ("MBON07", "MBON11"):
        use = target_types == name
        mass[name] = np.bincount(c["pre"][use], weights=contacts[use], minlength=brain.n).astype(np.int64)
    both = np.flatnonzero((mass["MBON07"] > 0) & (mass["MBON11"] > 0))
    groups = {"A": [], "B": []}
    for side in ("L", "R"):
        candidates = [int(i) for i in both if str(annotation.instance.iloc[i]).endswith("_" + side)]
        candidates.sort(key=lambda i: (-min(mass["MBON07"][i], mass["MBON11"][i]),
                                       -int(mass["MBON07"][i] + mass["MBON11"][i]), int(brain.ids[i])))
        if len(candidates) < 16:
            raise RuntimeError("Insufficient anatomically supported cue neurons")
        groups["A"].extend(candidates[:16:2])
        groups["B"].extend(candidates[1:16:2])
    groups = {k: np.asarray(v, dtype=np.int32) for k, v in groups.items()}
    assert not np.intersect1d(groups["A"], groups["B"]).size
    report = {k: {"ids": brain.ids[v].tolist(), "indices": v.tolist(),
                  "types": annotation.type.iloc[v].tolist(),
                  "contacts": {t: int(mass[t][v].sum()) for t in mass},
                  "plastic_edges": int(np.isin(c["pre"], v).sum())} for k, v in groups.items()}
    return groups, report


def memory_stats(brain, groups, outputs):
    c = brain.circuit
    fraction = brain.weight[c["edges"]] / brain.baseline_plastic
    by_input = {}
    for cue, ix in {**groups, "unstimulated": np.setdiff1d(c["kc"], np.r_[groups["A"], groups["B"]])}.items():
        by_input[cue] = {}
        for target, cells in outputs.items():
            mask = np.isin(c["pre"], ix) & np.isin(brain.post[c["edges"]], cells)
            by_input[cue][target] = {
                "edges": int(mask.sum()),
                "weighted_efficacy": float(brain.weight[c["edges"][mask]].sum() / brain.baseline_plastic[mask].sum()),
                "changed_edges": int(np.count_nonzero(fraction[mask] != 1)),
            }
    return {"weight_sha256": hashlib.sha256(brain.weight[c["edges"]].tobytes()).hexdigest(),
            "u_sha256": hashlib.sha256(brain.memory_u.tobytes()).hexdigest(),
            "w_sha256": hashlib.sha256(brain.memory_w.tobytes()).hexdigest(),
            "changed_edges": int(np.count_nonzero(fraction != 1)),
            "at_lower_bound": int(np.count_nonzero(fraction <= 0.100001)),
            "at_upper_bound": int(np.count_nonzero(fraction >= 1.999999)), "by_input": by_input}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("probe", "train"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reference", type=Path, help="Completed label-blind probe directory; required for training")
    parser.add_argument("--cue-current", type=float, default=30)
    parser.add_argument("--pulse-current", type=float, default=20)
    parser.add_argument("--eta", type=float, default=0.001)
    args = parser.parse_args()
    if any(not np.isfinite(x) or x <= 0 for x in (args.cue_current, args.pulse_current, args.eta)):
        parser.error("Currents and eta must be finite and positive")
    if args.mode == "train" and args.reference is None:
        parser.error("Training requires a completed label-blind probe")
    head = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    if head != UPSTREAM_COMMIT or dirty:
        parser.error("Upstream must be the clean pinned commit")
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    os.environ["STONKFLY_DATA"] = str(ROOT / "data")
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.brain import MemoryBrain
    from stonkfly.neural.common import annotations

    verified = verify()
    started = time.perf_counter()
    brain = MemoryBrain(eta=args.eta)
    annotation = annotations(brain.ids)
    groups, group_report = select_cues(brain, annotation)
    outputs = {t: np.flatnonzero(annotation.type.eq(t)) for t in ("MBON07", "MBON11")}
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    initial_all_weights = hashlib.sha256(brain.weight.tobytes()).hexdigest()
    offset = 0.0
    orders = []
    for seed in (20260911, 20260912):
        order = ["A", "B"] * 4
        random.Random(seed).shuffle(order)
        inconsistent = [None] * 8
        for cue in ("A", "B"):
            positions = [i for i, x in enumerate(order) if x == cue]
            pulses = ["reward", "reward", "aversive", "aversive"]
            random.Random(seed + (0 if cue == "A" else 100)).shuffle(pulses)
            for i, pulse in zip(positions, pulses):
                inconsistent[i] = pulse
        orders.append({"seed": seed, "cues": order, "inconsistent_pulses": inconsistent})
    protocol = {
        "experiment": "004-direct-conditioning", "mode": args.mode,
        "claim_scope": "Synthetic KC-to-valence conditioning, not visual cue learning, chosen-action reinforcement, or Sudoku.",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "imported_source_sha256": hashlib.sha256((ROOT / "sudokufly.py").read_bytes()).hexdigest(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "upstream_head": head, "graph": verified, "initial_weights_sha256": initial_all_weights,
        "dependencies": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "pyarrow", "Pillow")},
        "circuit": brain.circuit["report"], "cue_groups": group_report,
        "selection": "Within each hemisphere rank shared KC inputs by descending minimum compartment contacts, then total contacts, then body ID; alternate first16 into A/B.",
        "cue_current": args.cue_current, "pulse_current": args.pulse_current, "eta": args.eta,
        "rule": brain.rule_parameters,
        "sensory": "No retinal input, zero lamina bias, no additional tonic drive. Whole original MemoryBrain graph retained.",
        "timing_ms": {"cue": 500, "cue_off_feedback": 200, "passive_consolidation": 250},
        "learning": "Cue: freeze weights, accumulate traces. Feedback: remove imposed KC current, stimulate assigned DANs, enable local rule. Consolidation: disable associative drive, permit passive u/w relaxation. Reset electrical state/traces between trials; retain weights/u/w.",
        "pairing": "Pavlovian: assigned valence determines pulse, independent of decoded response. Reverse assignments in separate baseline-start runs.",
        "orders": orders,
        "decoder": {"raw": "mean MBON11 Hz minus mean MBON07 Hz", "offset_hz": 0.0,
                    "threshold_hz": 5.0, "positive": "accept/reward", "negative": "reject/aversive",
                    "calibration": "One global offset from pooled untrained A/B raw scores; no labels or trained outputs. All coefficients, offset and threshold frozen before training."},
        "gates": {"all_four_mapping_order_runs": "100% paired evaluation, above frozen/no-feedback/inconsistent controls in each run",
                  "mechanism": "Each cue has >=0.02 greater weighted efficacy depression in its paired compartment than in the other compartment",
                  "controls": "Exact frozen and erasure recovery; unchanged nonplastic weights; repeated frozen evaluations identical",
                  "visual_level_1_passed": False},
    }
    if args.mode == "train":
        reference = json.loads((args.reference / "summary.json").read_text())
        previous = json.loads((args.reference / "protocol.json").read_text())
        for key in ("source_sha256", "imported_source_sha256", "cue_groups", "cue_current", "pulse_current", "eta", "initial_weights_sha256"):
            if previous[key] != protocol[key]:
                raise RuntimeError(f"Probe protocol differs: {key}")
        offset = float(reference["decoder_offset_hz"])
        protocol["decoder"]["offset_hz"] = offset
        protocol["reference"] = {"path": os.path.relpath(args.reference.resolve(), args.out),
                                 "summary_sha256": hashlib.sha256((args.reference / "summary.json").read_bytes()).hexdigest()}
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    rows = []
    results = []
    log = (args.out / "trials.jsonl").open("x")

    def measure(duration, *, stimulus=None, learning=False, frozen=True):
        brain.weights_frozen = frozen
        before = memory_stats(brain, groups, outputs)
        total = np.zeros(brain.n, dtype=np.int32)
        bins = []
        for _ in range(duration // 10):
            counts, _ = brain.step(dark, 10, stimulation=stimulus, learning=learning, lamina_bias=0)
            total += counts
            bins.append({"KC_A": int(counts[groups["A"]].sum()), "KC_B": int(counts[groups["B"]].sum()),
                         "KC_all": int(counts[brain.circuit["kc"]].sum()),
                         "reward": int(counts[brain.circuit["reward"]].sum()),
                         "aversive": int(counts[brain.circuit["aversive"]].sum()),
                         **{t: counts[ix].tolist() for t, ix in outputs.items()}})
        hz = {t: (total[ix] * 1000 / duration).tolist() for t, ix in outputs.items()}
        raw = float(np.mean(hz["MBON11"]) - np.mean(hz["MBON07"]))
        centered = raw - offset
        after = memory_stats(brain, groups, outputs)
        if frozen and before != after:
            raise RuntimeError("Frozen phase changed memory")
        return {"duration_ms": duration, "learning": learning, "frozen": frozen,
                "KC_A_spikes": int(total[groups["A"]].sum()), "KC_B_spikes": int(total[groups["B"]].sum()),
                "KC_all_spikes": int(total[brain.circuit["kc"]].sum()),
                "active_KCs": int(np.count_nonzero(total[brain.circuit["kc"]])),
                "DAN_spikes": {t: int(total[brain.circuit[t]].sum()) for t in ("reward", "aversive")},
                "output_hz": hz, "raw_score_hz": raw, "score_hz": centered,
                "action": "accept" if centered >= 5 else "reject" if centered <= -5 else "timeout",
                "spikes_sha256": hashlib.sha256(total.tobytes()).hexdigest(),
                "memory_before": before, "memory_after": after, "bins": bins}

    def record(context, row):
        row = {**context, **row}
        rows.append(row)
        log.write(json.dumps(row, allow_nan=False) + "\n")
        log.flush()
        print(json.dumps({k: row[k] for k in (*context.keys(), "score_hz", "action", "KC_all_spikes")}), flush=True)
        return row

    def evaluate(context, targets):
        evaluations = []
        for cue in ("A", "B", "A", "B"):
            brain.reset(keep_memory=True)
            row = measure(500, stimulus=(groups[cue], args.cue_current))
            evaluations.append(record({**context, "cue": cue, "target": targets[cue],
                                       "correct": row["action"] == targets[cue]}, row))
        if any(x["spikes_sha256"] != y["spikes_sha256"] for x, y in zip(evaluations[:2], evaluations[2:])):
            raise RuntimeError("Frozen evaluation is not repeatable")
        return evaluations

    if args.mode == "probe":
        brain.reset(keep_memory=False)
        record({"phase": "silent", "cue": None}, measure(500))
        baseline = evaluate({"phase": "untrained"}, {"A": "unassigned", "B": "unassigned"})
        for cue in ("A", "B"):
            brain.reset(keep_memory=False)
            measure(500, stimulus=(groups[cue], args.cue_current))
            record({"phase": "cue_offset", "cue": cue}, measure(200))
            record({"phase": "late", "cue": cue}, measure(250))
        result = {"decoder_offset_hz": float(np.mean([r["raw_score_hz"] for r in baseline])),
                  "untrained_raw_scores_hz": {r["cue"]: r["raw_score_hz"] for r in baseline},
                  "no_learning_performed": True}
    else:
        for order_id, schedule in enumerate(orders):
            for mapping in (0, 1):
                valence = {cue: "reward" if i == mapping else "aversive" for i, cue in enumerate(("A", "B"))}
                targets = {cue: "accept" if pulse == "reward" else "reject" for cue, pulse in valence.items()}
                brain.reset(keep_memory=False)
                baseline = evaluate({"order": order_id, "mapping": mapping, "arm": "baseline", "phase": "eval"}, targets)
                baseline_hashes = [r["spikes_sha256"] for r in baseline]
                arms = {}
                for arm in ("paired", "frozen", "no_feedback", "inconsistent"):
                    brain.reset(keep_memory=False)
                    for trial, cue in enumerate(schedule["cues"]):
                        brain.reset(keep_memory=True)
                        context = {"order": order_id, "mapping": mapping, "arm": arm, "trial": trial, "cue": cue}
                        record({**context, "phase": "cue"}, measure(500, stimulus=(groups[cue], args.cue_current)))
                        pulse = None if arm == "no_feedback" else schedule["inconsistent_pulses"][trial] if arm == "inconsistent" else valence[cue]
                        stimulus = None if pulse is None else (brain.circuit[pulse], args.pulse_current)
                        record({**context, "phase": "feedback", "pulse": pulse},
                               measure(200, stimulus=stimulus, learning=arm != "frozen", frozen=arm == "frozen"))
                        record({**context, "phase": "consolidation"}, measure(250, frozen=arm == "frozen"))
                    memory = memory_stats(brain, groups, outputs)
                    np.savez_compressed(args.out / f"order-{order_id}-mapping-{mapping}-{arm}-memory.npz",
                                        edge_indices=brain.circuit["edges"], weights=brain.weight[brain.circuit["edges"]],
                                        u=brain.memory_u, w=brain.memory_w)
                    evaluations = evaluate({"order": order_id, "mapping": mapping, "arm": arm, "phase": "eval"}, targets)
                    saved_weights = brain.weight[brain.circuit["edges"]].copy()
                    brain.weight[brain.circuit["edges"]] = brain.baseline_plastic
                    nonplastic_unchanged = hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_all_weights
                    brain.weight[brain.circuit["edges"]] = saved_weights
                    if not nonplastic_unchanged:
                        raise RuntimeError("A nonplastic connection changed")
                    brain.reset(keep_memory=False)
                    erased = evaluate({"order": order_id, "mapping": mapping, "arm": arm, "phase": "erased"}, targets)
                    recovery = [r["spikes_sha256"] for r in erased] == baseline_hashes
                    if not recovery:
                        raise RuntimeError("Memory erasure did not recover baseline")
                    if arm == "frozen" and [r["spikes_sha256"] for r in evaluations] != baseline_hashes:
                        raise RuntimeError("Frozen control differs from baseline")
                    margins = {}
                    for cue, pulse in valence.items():
                        paired_target = "MBON07" if pulse == "reward" else "MBON11"
                        other = "MBON11" if pulse == "reward" else "MBON07"
                        margins[cue] = memory["by_input"][cue][other]["weighted_efficacy"] - memory["by_input"][cue][paired_target]["weighted_efficacy"]
                    arms[arm] = {"accuracy": sum(r["correct"] for r in evaluations) / len(evaluations),
                                 "scores_hz": {r["cue"]: r["score_hz"] for r in evaluations},
                                 "memory": memory, "paired_depression_margin": margins,
                                 "nonplastic_unchanged": nonplastic_unchanged, "erasure_recovers_baseline": recovery}
                passed = arms["paired"]["accuracy"] == 1 and all(arms["paired"]["accuracy"] > arms[x]["accuracy"] for x in ("frozen", "no_feedback", "inconsistent")) and all(x >= 0.02 for x in arms["paired"]["paired_depression_margin"].values())
                results.append({"order": order_id, "mapping": mapping, "arms": arms, "calibration_gate_passed": passed})
                (args.out / "partial-results.json").write_text(json.dumps(results, indent=2) + "\n")
        result = {"runs": results, "calibration_gate_passed": all(r["calibration_gate_passed"] for r in results)}
    log.close()
    result.update({"visual_level_1_passed": False, "elapsed_seconds": time.perf_counter() - started,
                   "recorded_phases": len(rows),
                   "files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.out.iterdir()) if p.is_file()}})
    (args.out / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"complete": str(args.out), "elapsed_seconds": result["elapsed_seconds"],
                      "calibration_gate_passed": result.get("calibration_gate_passed")}), flush=True)


if __name__ == "__main__":
    main()
