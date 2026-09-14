"""Development-only joint rehearsal through existing fly synapses.

The candidate/Undo encoders and decoder are fixed. Supervised labels affect
only dopamine timing during teaching, never the inputs or episode actions.
"""

import argparse
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np

from compare_symbols import balanced_groups
from constraint_transfer import render_partial
from learn_undo import play_with_undo
from one_blank import classification_metrics
from sequence_sudoku import POLICIES, SOURCE, encode_sequence, probe_metrics
from sudokufly import ROOT, UPSTREAM, UPSTREAM_COMMIT, memory_state


def encode_occupancy(frame, templates, groups, occupancy_groups):
    """Route generic candidate/peer identities through the observed-count bank.

    Pixel recognition, target attention, deduplication and capped KC counts are
    unchanged. Neither equality, legality nor a teaching label selects a bank.
    The original three-peer bank and silent empty input are retained exactly.
    """
    inherited, diagnostic = encode_sequence(frame, templates, groups, "capped-24")
    count = diagnostic["distinct_peers"]
    if count not in occupancy_groups:
        return inherited, diagnostic
    candidate = diagnostic["candidate_template"]
    peers = diagnostic["peer_templates"]
    per_side = min(8, 12 // count)
    bank = occupancy_groups[count]
    indices = np.sort(np.concatenate([bank[candidate * 4 + peer, :, :per_side].ravel()
                                      for peer in peers]))
    assert len(indices) == len(np.unique(indices)) == len(inherited)
    return indices, diagnostic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=ROOT / "experiments/level-05/003-shorter-undo/development")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--separate-occupancies", action="store_true")
    parser.add_argument("--margin-hz", type=float, default=3.0)
    args = parser.parse_args()
    if args.epochs < 1 or not np.isfinite(args.margin_hz) or args.margin_hz < 2:
        parser.error("Positive epoch budget and teaching margin at least2Hz required")
    started = time.perf_counter()
    prior = ROOT / "experiments/level-05/001-variable-peers/development"
    args.source = args.source.resolve()
    source_summary = json.loads((args.source / "summary.json").read_text())
    assert len(source_summary["runs"]) == 4
    assert {(r["seed"], r["mapping"]) for r in source_summary["runs"]} == {(seed, mapping) for seed in (20260919, 20260920) for mapping in (0, 1)}
    source_protocol = json.loads((args.source / "protocol.json").read_text())
    config = json.loads((SOURCE / "protocol.json").read_text())
    prior_summary = json.loads((prior / "summary.json").read_text())
    for directory, summary in ((args.source, source_summary), (prior, prior_summary)):
        for name, digest in summary["files_sha256"].items():
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest
    upstream = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    assert upstream == UPSTREAM_COMMIT and not dirty
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    os.environ["STONKFLY_DATA"] = str(ROOT / "data")
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.brain import MemoryBrain
    from stonkfly.neural.common import annotations

    graph = verify()
    params = config["source_parameters"]
    brain = MemoryBrain(eta=params["eta"])
    c = brain.circuit
    annotation = annotations(brain.ids)
    outputs = {name: np.flatnonzero(annotation.type.eq(name)) for name in ("MBON07", "MBON11")}
    for ix in outputs.values():
        brain.tonic[ix] = config["inference_mbon_current"]
    initial_hash = hashlib.sha256(brain.weight.tobytes()).hexdigest()
    assert initial_hash == config["initial_weights_sha256"] == source_protocol["initial_weights_sha256"]
    positions = {int(cell): i for i, cell in enumerate(brain.ids)}
    sp_path = ROOT / config["memory_source"] / "protocol.json"
    assert hashlib.sha256(sp_path.read_bytes()).hexdigest() == config["memory_protocol_sha256"]
    sp = json.loads(sp_path.read_text())
    templates = np.array(sp["templates"], dtype=np.float64)
    groups = np.array([positions[int(cell)] for cell in np.array(sp["group_KC_ids"]).ravel()], dtype=np.int32).reshape(16, 2, 8)
    undo_groups = np.array([positions[int(cell)] for cell in np.array(source_protocol["undo_KC_ids"]).ravel()], dtype=np.int32).reshape(16, 16)
    inputs = {key: np.array([positions[int(cell)] for cell in row["KC_ids"]], dtype=np.int32)
              for key, row in json.loads((args.source / "inputs.json").read_text()).items()}
    assert len(inputs) == 121 and all(hashlib.sha256(ix.tobytes()).hexdigest() == k for k, ix in inputs.items())
    inherited_input_keys = set(inputs)
    place_contexts = json.loads((prior / "contexts.json").read_text())
    primary_policy = "separate-occupancy" if args.separate_occupancies else "capped-24"
    policies_to_report = (*POLICIES, "separate-occupancy") if args.separate_occupancies else POLICIES
    occupancy_groups, occupancy_anatomy = {}, {}
    if args.separate_occupancies:
        # Select from original anatomy, before any inherited memory is loaded.
        contacts = np.rint(brain.baseline_plastic / 0.275).astype(np.int64)
        mass = {}
        for name, ix in outputs.items():
            keep = np.isin(brain.post[c["edges"]], ix)
            mass[name] = np.bincount(c["pre"][keep], weights=contacts[keep], minlength=brain.n)
        both = np.flatnonzero((mass["MBON07"] > 0) & (mass["MBON11"] > 0))
        excluded = set(groups.ravel().tolist()) | set(undo_groups.ravel().tolist())
        ranked = {}
        for side in ("L", "R"):
            choices = [int(i) for i in both if i not in excluded and str(annotation.instance.iloc[i]).endswith("_" + side)]
            choices.sort(key=lambda i: (-min(mass["MBON07"][i], mass["MBON11"][i]),
                                        -(mass["MBON07"][i] + mass["MBON11"][i]), int(brain.ids[i])))
            assert len(choices) >= 384
            ranked[side] = choices
        for rank, count in enumerate((1, 2, 4)):
            pool = np.array(ranked["L"][128 * rank:128 * (rank + 1)] +
                            ranked["R"][128 * rank:128 * (rank + 1)], dtype=np.int32)
            bank, _, report = balanced_groups(brain, pool, np.concatenate(list(outputs.values())))
            occupancy_groups[count] = bank.reshape(16, 2, 8)
            assert not set(bank.ravel().tolist()) & excluded
            excluded.update(bank.ravel().tolist())
            occupancy_anatomy[str(count)] = report
        original_contexts = [r for r in place_contexts if r["policy"] == "capped-24"]
        for row in original_contexts:
            board = [0] * 16
            for position, digit in zip((1, 2, 4, 5), row["peers"]):
                board[position] = digit
            keys = set()
            for view in ("base", "shift", "small"):
                frame = render_partial(board, 0, row["candidate"], view)
                indices, diagnostic = encode_occupancy(frame, templates, groups, occupancy_groups)
                key = hashlib.sha256(indices.tobytes()).hexdigest()
                inputs.setdefault(key, indices)
                keys.add(key)
                assert diagnostic["distinct_peers"] == row["distinct_peers"]
            assert len(keys) == 1
            assert (key == row["input"]) == (row["distinct_peers"] in (0, 3))
            place_contexts.append({**row, "policy": primary_policy, "input": key, "active_KCs": len(indices)})
        assert len(inputs) == 165 and len(set(inputs) - inherited_input_keys) == 44
    placement_encoder = (lambda frame, templates, groups, policy:
                         encode_occupancy(frame, templates, groups, occupancy_groups)) if args.separate_occupancies else None
    undo_contexts = json.loads((args.source / "undo-contexts.json").read_text())
    cases = json.loads((prior / "cases.json").read_text())
    familiar = {r["input"]: r["label"] for r in place_contexts if r["policy"] == "capped-24" and r["distinct_peers"] == 3}
    training = [{"operation": "place", "input": r["input"], "label": r["label"], "distinct_peers": r["distinct_peers"]}
                for r in place_contexts if r["policy"] == primary_policy and r["distinct_peers"] > 0]
    training.extend({"operation": "undo", "input": r["input"], "label": r["label"], "pattern": r["pattern"]} for r in undo_contexts)
    assert len(training) == len({r["input"] for r in training}) == 76
    schedules = {}
    for seed in (20260919, 20260920):
        epochs = []
        for epoch in range(args.epochs):
            order = list(range(len(training)))
            random.Random(seed + 1000 * epoch + 170000).shuffle(order)
            epochs.append(order)
        schedules[str(seed)] = epochs
    for name, data in (("training-contexts.json", training), ("schedules.json", schedules),
                       ("contexts.json", place_contexts),
                       ("inputs.json", {key: {"KC_ids": brain.ids[ix].tolist()} for key, ix in inputs.items()})):
        (args.out / name).write_text(json.dumps(data, indent=2) + "\n")
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
              ("joint_sudoku.py", "learn_undo.py", "sequence_sudoku.py", "constraint_transfer.py", "one_blank.py", "compare_symbols.py", "sudokufly.py")}
    historical_sources = {}
    for name, digest in source_protocol["source_sha256"].items():
        historical = subprocess.check_output(["git", "show", f"{source_protocol['git_head']}:{name}"], cwd=ROOT)
        assert hashlib.sha256(historical).hexdigest() == digest
        historical_sources[name] = digest
        if name != "learn_undo.py":
            assert hashes[name] == digest
        elif hashes[name] != digest:
            # Only the episode driver's optional encoder extension may differ;
            # rendering, Undo encoding, imports and neural training remain exact.
            old_nodes = [n for n in ast.parse(historical).body
                         if not isinstance(n, ast.FunctionDef) or n.name != "play_with_undo"]
            new_nodes = [n for n in ast.parse((ROOT / name).read_text()).body
                         if not isinstance(n, ast.FunctionDef) or n.name != "play_with_undo"]
            assert [ast.dump(n, include_attributes=False) for n in old_nodes] == [ast.dump(n, include_attributes=False) for n in new_nodes]
    offset, threshold = (config["decoder"][name] for name in ("offset_hz", "threshold_hz"))
    protocol = {
        "task": "Paired-only development pilot: joint placement/Undo margin rehearsal",
        "separate_occupancies": args.separate_occupancies,
        "historical_source_git_head": source_protocol["git_head"], "historical_source_sha256": historical_sources,
        "inherited_input_count": len(inherited_input_keys), "new_input_count": len(inputs) - len(inherited_input_keys),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": hashes, "upstream": upstream, "graph": graph, "initial_weights_sha256": initial_hash,
        "memory_source": str(args.source.relative_to(ROOT)),
        "memory_summary_sha256": hashlib.sha256((args.source / "summary.json").read_bytes()).hexdigest(),
        "configuration_source": str(SOURCE.relative_to(ROOT)),
        "configuration_sha256": hashlib.sha256((SOURCE / "protocol.json").read_bytes()).hexdigest(),
        "prior_assay": str(prior.relative_to(ROOT)), "prior_summary_sha256": hashlib.sha256((prior / "summary.json").read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256((prior / "cases.json").read_bytes()).hexdigest(),
        "parameters": {"KC_current": params["kc_current"], "MBON_current": config["inference_mbon_current"],
                       "eta": params["eta"], "DAN_current": 20, "duration_ms": 500},
        "decoder": {"offset_hz": offset, "threshold_hz": threshold},
        "undo_KC_ids": brain.ids[undo_groups].tolist(), "primary_policy": primary_policy,
        "occupancy_KC_ids": {str(n): brain.ids[bank].tolist() for n, bank in occupancy_groups.items()},
        "occupancy_anatomy": occupancy_anatomy,
        "sensory_routing": "Separate mode assigns generic observed peer counts1,2,4 to disjoint candidate-by-peer banks. Each256-cell bank uses128 cells per side from consecutive anatomy-ranked unused slices, then the unchanged balanced partition. Count3 retains the original bank; count0 stays silent. No task labels, equality checks or inferred legality enter routing; capped active-cell counts stay0,16,24,24,24. Without separate mode, the original capped24 bank is used at every count.",
        "selection_reason": "Original capped24 was selected using001; separate mode tests whether disjoint generic occupancy routing reduces shared-synapse interference. Both old policies remain diagnostic probe reports. New-policy controls are unassessed in this pilot.",
        "maximum_epochs": args.epochs, "teaching_signed_score_hz": args.margin_hz,
        "training": "Each epoch presents all60 nonempty primary-policy placement contexts and16 Undo contexts once, in a saved seeded order. Frozen500ms observation; teach iff label-signed fixed-decoder score is below the recorded margin. Existing bidirectional targetDAN200 learning/passive250/reset/oppositeDAN200 frozen/cue500 learning/passive250. Otherwise the trial stays fully frozen. Teaching labels never enter inputs or runtime decisions. Passive decay remains active during every nonfrozen window.",
        "evaluation": f"Evaluate{len(inputs)} inputs from reset with W/u/w frozen at inheritance and after each epoch; save every memory. All121 inherited source inputs must exactly reproduce their source responses; new inputs receive measured inherited references. Exact full-weight before/after checks for every frozen batch. No independent-sample claim for response reuse.",
        "stopping": "Stop each condition at its FIRST epoch passing placement, retention, Undo recall AND every development recovery stratum, or at the fixed epoch cap. Preserve every attempted epoch and failed case. This development selection requires subsequent controlled reproduction and reserved-family confirmation.",
        "gates": {"placement_nonempty_balanced_accuracy": .90, "placement_occupancy_class_recall": .85,
                  "old_policy_gain_over_original_history_controls": .25,
                  "new_policy_control_gain": None, "familiar_retention": 1.0,
                  "undo_balanced_accuracy": .90, "undo_class_recall": .85, "sequence_per_stratum": .90},
        "controls_evaluated": False, "heldout_evaluated": False, "stage5_complete": False,
        "limits": "Development checkpoint selection only. Encoders, target attention, menu and stack are engineered. No host legality filter, automatic Undo or branch cursor. Empty-peer input stays silent and outside the nonempty gate. Rehearsal can fail or interfere; no selective weight clamping/restoration during training. A pilot pass does not itself prove added-teaching necessity or finish Step5."}
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    source_recall = {}
    for line in (args.source / "neural.jsonl").open():
        row = json.loads(line)
        if row["phase"] == "recall" and row["arm"] == "paired":
            source_recall[row["seed"], row["mapping"], row["input"]] = row
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    neural_log = (args.out / "neural.jsonl").open("x")
    training_log = (args.out / "training.jsonl").open("x")
    weight_checks, references = [], []
    measured = 0

    def measure(indices=None, duration=500, pulse=None, learning=False, frozen=True, traced=False):
        brain.weights_frozen = frozen
        before = memory_state(brain)
        stimulation = [] if indices is None else [(indices, params["kc_current"])]
        if pulse is not None:
            stimulation.append((c[pulse], 20))
        boundaries = list(range(0, 101, 4)) + list(range(110, 501, 10)) if traced else [0, duration]
        counts = np.zeros(brain.n, dtype=np.int32)
        trace = []
        for start, end in zip(boundaries, boundaries[1:]):
            chunk, _ = brain.step(dark, end - start, stimulation=stimulation, learning=learning, lamina_bias=0)
            counts += chunk
            if traced:
                trace.append({"start_ms": start, "end_ms": end, "selected_KC_counts": chunk[indices].tolist(),
                              "output_counts": {name: chunk[ix].tolist() for name, ix in outputs.items()}})
        hz = {name: float(counts[ix].mean() * 1000 / duration) for name, ix in outputs.items()}
        score = hz["MBON11"] - hz["MBON07"] - offset
        after = memory_state(brain)
        if frozen:
            assert before == after
        return {"duration_ms": duration, "pulse": pulse, "learning": learning, "frozen": frozen,
                "output_hz": hz, "score_hz": score, "action": 1 if score >= threshold else 0 if score <= -threshold else -1,
                "spikes_sha256": hashlib.sha256(counts.tobytes()).hexdigest(), "memory_before": before, "memory_after": after,
                "trace": trace, "KC_spikes": int(counts[c["kc"]].sum()),
                "DAN_spikes": {name: int(counts[c[name]].sum()) for name in ("reward", "aversive")}}

    def evaluate(context, expected=None):
        nonlocal measured
        full_before = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        responses = {}
        for key, indices in inputs.items():
            brain.reset(keep_memory=True)
            row = measure(indices, traced=True)
            if expected is not None and key in expected:
                assert all(row[field] == expected[key][field] for field in ("spikes_sha256", "score_hz", "action", "trace", "memory_before", "memory_after"))
            neural_log.write(json.dumps({**context, "input": key, **row}) + "\n")
            responses[key] = row
            measured += 1
        neural_log.flush()
        full_after = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        assert full_before == full_after
        weight_checks.append({**context, "before_sha256": full_before, "after_sha256": full_after})
        return responses

    def score(responses, mapping, prior_run):
        policies = {}
        for policy in policies_to_report:
            rows = [r for r in place_contexts if r["policy"] == policy]
            raw = [responses[r["input"]]["action"] for r in rows]
            semantic = [a if a == -1 else a ^ mapping for a in raw]
            scored = probe_metrics(rows, semantic)
            absolute_gate = (scored["nonempty"]["balanced_accuracy"] >= .90 and
                             all(v >= .85 for n, group in scored["by_distinct_peers"].items() if n != "0" for v in group["class_recall"].values()))
            control_gains = ({arm: scored["nonempty"]["balanced_accuracy"] -
                             prior_run["arms"][arm]["policies"][policy]["probe"]["nonempty"]["balanced_accuracy"]
                             for arm in ("frozen", "no_feedback", "inconsistent")} if policy in POLICIES else None)
            control_gate = all(gain >= .25 for gain in control_gains.values()) if control_gains is not None else None
            gate = absolute_gate and (control_gate if control_gate is not None else True)
            policies[policy] = {"metrics": scored, "absolute_gate": absolute_gate,
                                "original_history_control_gains": control_gains,
                                "original_history_control_gate": control_gate, "gate": gate}
        raw = [responses[r["input"]]["action"] for r in undo_contexts]
        semantic = np.array([a if a == -1 else a ^ mapping for a in raw])
        undo = classification_metrics(np.array([r["label"] for r in undo_contexts]), semantic)
        retained = sum(responses[k]["action"] == (label ^ mapping) for k, label in familiar.items())
        gate = policies[primary_policy]["gate"] and retained == 16 and undo["balanced_accuracy"] >= .90 and min(undo["class_recall"].values()) >= .85
        return {"policies": policies, "familiar_correct": retained, "undo": undo, "joint_judgment_gate": gate}

    brain.reset(keep_memory=False)
    baseline = evaluate({"phase": "baseline"})
    results = []
    with gzip.open(args.out / "episodes.jsonl.gz", "xt", compresslevel=6) as episodes:
        for source_run in source_summary["runs"]:
            seed, mapping = source_run["seed"], source_run["mapping"]
            prior_run = next(r for r in prior_summary["runs"] if r["seed"] == seed and r["mapping"] == mapping)
            path = args.source / f"{seed}-{mapping}-paired-memory.npz"
            with np.load(path, allow_pickle=False) as saved:
                assert np.array_equal(saved["edge_indices"], c["edges"])
                inherited_weights, inherited_u, inherited_w = (saved[k].copy() for k in ("weights", "u", "w"))
            references.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            brain.reset(keep_memory=False)
            brain.weight[c["edges"]], brain.memory_u[:], brain.memory_w[:] = inherited_weights, inherited_u, inherited_w
            assert memory_state(brain) == source_run["arms"]["paired"]["memory"]
            inherited_full = hashlib.sha256(brain.weight.tobytes()).hexdigest()
            inherited = evaluate({"seed": seed, "mapping": mapping, "phase": "inherited"},
                                 {k: source_recall[seed, mapping, k] for k in inherited_input_keys})
            history = []
            selected_epoch = None
            for epoch, order in enumerate(schedules[str(seed)], 1):
                teaching_events = 0
                for trial, index in enumerate(order):
                    item = training[index]
                    target = item["label"] ^ mapping
                    brain.reset(keep_memory=True)
                    decision = measure(inputs[item["input"]])
                    teach = (1 if target else -1) * decision["score_hz"] < args.margin_hz
                    phases = []
                    if teach:
                        teaching_events += 1
                        pulse = "reward" if target else "aversive"
                        phases.extend([measure(duration=200, pulse=pulse, learning=True, frozen=False),
                                       measure(duration=250, frozen=False)])
                        brain.reset(keep_memory=True)
                        opposite = "aversive" if target else "reward"
                        phases.extend([measure(duration=200, pulse=opposite),
                                       measure(inputs[item["input"]], learning=True, frozen=False),
                                       measure(duration=250, frozen=False)])
                    training_log.write(json.dumps({"seed": seed, "mapping": mapping, "epoch": epoch, "trial": trial,
                                                   "context": index, "input": item["input"], "target": target,
                                                   "teach": teach, "decision": decision, "phases": phases}) + "\n")
                training_log.flush()
                checkpoint = args.out / f"{seed}-{mapping}-epoch-{epoch:02d}-memory.npz"
                state = memory_state(brain)
                np.savez_compressed(checkpoint, edge_indices=c["edges"], weights=brain.weight[c["edges"]], u=brain.memory_u, w=brain.memory_w)
                responses = evaluate({"seed": seed, "mapping": mapping, "phase": "recall", "epoch": epoch})
                scored = score(responses, mapping, prior_run)
                sequence = None
                if scored["joint_judgment_gate"] or epoch == args.epochs:
                    completed = []
                    for case in cases:
                        if case["split"] != "development":
                            continue
                        result = play_with_undo(case, responses, templates, groups, undo_groups, primary_policy, mapping,
                                                placement_encoder=placement_encoder)
                        episodes.write(json.dumps({"seed": seed, "mapping": mapping, "epoch": epoch, "policy": primary_policy, **result}) + "\n")
                        completed.append(result)
                    sequence = {f"{blanks}-{stratum}": {"puzzles": len(subset), "solved": sum(r["solved"] for r in subset),
                                "solve_rate": float(np.mean([r["solved"] for r in subset]))}
                                for blanks in (2, 3, 4) for stratum in ("easy", "trap")
                                for subset in [[r for r in completed if r["blanks"] == blanks and r["stratum"] == stratum]] if subset}
                passed = scored["joint_judgment_gate"] and sequence is not None and all(r["solve_rate"] >= .90 for r in sequence.values())
                history.append({"epoch": epoch, "teaching_events": teaching_events, "memory": state,
                                "checkpoint": checkpoint.name, "scores": scored, "sequence": sequence, "pilot_gate": passed})
                print(json.dumps({"seed": seed, "mapping": mapping, "epoch": epoch, "teaching_events": teaching_events,
                                  "placement": scored["policies"][primary_policy]["metrics"]["nonempty"]["balanced_accuracy"],
                                  "n4": scored["policies"][primary_policy]["metrics"]["by_distinct_peers"]["4"]["class_recall"],
                                  "familiar": scored["familiar_correct"], "undo": scored["undo"]["balanced_accuracy"], "passed": passed}), flush=True)
                (args.out / f"{seed}-{mapping}-history.json").write_text(json.dumps(history, indent=2) + "\n")
                if passed:
                    selected_epoch = epoch
                    break
            brain.weight[c["edges"]] = brain.baseline_plastic
            assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_hash
            brain.reset(keep_memory=False)
            brain.weight[c["edges"]], brain.memory_u[:], brain.memory_w[:] = inherited_weights, inherited_u, inherited_w
            assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == inherited_full
            evaluate({"seed": seed, "mapping": mapping, "phase": "stage_erased"}, inherited)
            brain.reset(keep_memory=False)
            assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_hash
            evaluate({"seed": seed, "mapping": mapping, "phase": "erased"}, baseline)
            results.append({"seed": seed, "mapping": mapping, "selected_epoch": selected_epoch, "history": history,
                            "stage_erasure_exact": True, "full_erasure_exact": True, "nonplastic_unchanged": True})
            (args.out / "partial-results.json").write_text(json.dumps(results, indent=2) + "\n")
    neural_log.close()
    training_log.close()
    (args.out / "full-weight-checks.json").write_text(json.dumps(weight_checks, indent=2) + "\n")
    (args.out / "memory-references.json").write_text(json.dumps(references, indent=2) + "\n")
    summary = {"pilot_gate": all(r["selected_epoch"] is not None for r in results), "stage5_complete": False,
               "controls_evaluated": False, "heldout_evaluated": False, "primary_policy": primary_policy, "runs": results,
               "measured_neural_evaluations": measured, "elapsed_seconds": time.perf_counter() - started,
               "files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.out.iterdir()) if p.is_file()}}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"pilot_gate": summary["pilot_gate"], "stage5_complete": False, "seconds": summary["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
