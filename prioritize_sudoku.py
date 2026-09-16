"""Development pilot: learn Place/Defer in existing fly synapses.

The fixed selector compares neural scores for every offered cell/digit pair.
Only teaching and posthoc grading use Sudoku labels or solutions.
"""
import argparse
from collections import Counter
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

from confirm_sudoku import check_measure, records, require_committed, sha, verify_run
from constraint_transfer import render_partial
from joint_sudoku import encode_occupancy
from sequence_sudoku import valid_complete
from sudokufly import ROOT, UPSTREAM, UPSTREAM_COMMIT, memory_state

SOURCE = ROOT / "experiments/level-05/007-controlled-recovery/development"
SEED = 20260919
ARMS = ("paired", "frozen", "no_feedback", "inconsistent")


def play_ranked(board, responses, mapping, encode, view="base", budget=1024):
    """Fixed motor arbitration; only rendered observations and neural decisions."""
    initial = list(board)
    board, events, assessments = list(board), [], []
    offered = timeouts = 0
    while not all(board):
        choices = []
        before = list(board)
        for target in range(16):
            if board[target]:
                continue
            for candidate in range(1, 5):
                if offered >= budget:
                    return {"initial_board": initial, "final_board": board, "events": events,
                            "assessments": assessments, "neural_offers": offered,
                            "timeouts": timeouts, "end": "decision_budget"}
                frame = render_partial(board, target, candidate, view)
                indices, _ = encode(frame)
                key = hashlib.sha256(indices.tobytes()).hexdigest()
                row = responses[key]
                raw = row["action"]
                action = raw if raw == -1 else raw ^ mapping
                score = (1 - 2 * mapping) * row["score_hz"]
                choices.append({"target": target, "candidate": candidate, "input": key,
                                "raw_action": raw, "action": action, "score_hz": score,
                                "image_sha256": hashlib.sha256(frame.tobytes()).hexdigest()})
                offered += 1
                timeouts += action == -1
        # Ties stay in row-major, then digit order. No rule-based candidate mask.
        accepted = [row for row in choices if row["action"] == 1]
        chosen = max(accepted, key=lambda row: row["score_hz"]) if accepted else None
        assessments.append({"board": before, "offers": choices, "chosen": chosen})
        if chosen is None:
            break
        board[chosen["target"]] = chosen["candidate"]
        events.append({**chosen, "op": "place", "board_before": before,
                       "board_after": list(board), "assessment": len(assessments) - 1})
    assert all(not value or board[i] == value for i, value in enumerate(initial))
    return {"initial_board": initial, "final_board": board, "events": events,
            "assessments": assessments, "neural_offers": offered, "timeouts": timeouts,
            "end": "filled" if all(board) else "no_accepted_offer"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    source_summary, source_protocol = verify_run(SOURCE)
    paths = [Path(__file__), ROOT / "experiments/level-06/001-cautious-choice/README.md"]
    paths += [ROOT / name for name in source_protocol["source_sha256"]]
    require_committed(paths)
    assert all(sha(ROOT / name) == digest for name, digest in source_protocol["source_sha256"].items())
    assert subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip() == UPSTREAM_COMMIT
    assert not subprocess.check_output(["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    os.environ["STONKFLY_DATA"] = str(ROOT / "data")
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.brain import MemoryBrain
    from stonkfly.neural.common import annotations

    graph = verify()
    parameters, decoder = source_protocol["parameters"], source_protocol["decoder"]
    brain = MemoryBrain(eta=parameters["eta"])
    circuit = brain.circuit
    assert len(circuit["edges"]) == 7835
    annotation = annotations(brain.ids)
    outputs = {name: np.flatnonzero(annotation.type.eq(name)) for name in ("MBON07", "MBON11")}
    for indices in outputs.values():
        brain.tonic[indices] = parameters["MBON_current"]
    original_full = hashlib.sha256(brain.weight.tobytes()).hexdigest()
    assert original_full == source_protocol["initial_weights_sha256"]
    positions = {int(cell): i for i, cell in enumerate(brain.ids)}
    prior_protocol = json.loads((ROOT / source_protocol["memory_source"] / "protocol.json").read_text())
    template_path = ROOT / prior_protocol["memory_source"] / "protocol.json"
    assert sha(template_path) == prior_protocol["memory_protocol_sha256"]
    template_protocol = json.loads(template_path.read_text())
    templates = np.asarray(template_protocol["templates"], dtype=np.float64)
    groups = np.asarray([positions[int(cell)] for cell in np.asarray(template_protocol["group_KC_ids"]).ravel()], dtype=np.int32).reshape(16, 2, 8)
    occupancy = {int(n): np.asarray([positions[int(cell)] for cell in np.asarray(bank).ravel()], dtype=np.int32).reshape(16, 2, 8)
                 for n, bank in source_protocol["occupancy_KC_ids"].items()}
    encode = lambda frame: encode_occupancy(frame, templates, groups, occupancy)
    manifest = json.loads((SOURCE / "inputs.json").read_text())
    inputs = {key: np.asarray([positions[int(cell)] for cell in row["KC_ids"]], dtype=np.int32) for key, row in manifest.items()}
    assert len(inputs) == 165 and all(hashlib.sha256(ix.tobytes()).hexdigest() == key for key, ix in inputs.items())
    contexts = [r for r in json.loads((SOURCE / "contexts.json").read_text()) if r["policy"] == "separate-occupancy"]
    undo = json.loads((SOURCE / "undo-contexts.json").read_text())
    training = [{**row, "operation": "place", "old_label": row["label"],
                 "label": int(row["distinct_peers"] == 3 and row["label"] == 1)} for row in contexts if row["distinct_peers"]]
    training += [{**row, "operation": "undo", "old_label": row["label"]} for row in undo]
    assert len(training) == len({row["input"] for row in training}) == 76
    assert sum(row["label"] != row["old_label"] for row in training) == 24
    # Verify the inherited visual routing for all conceptual observations/views.
    for row in contexts:
        board = [0] * 16
        for position, digit in zip((1, 2, 4, 5), row["peers"]):
            board[position] = digit
        for view in ("base", "shift", "small"):
            ix, _ = encode(render_partial(board, 0, row["candidate"], view))
            assert hashlib.sha256(ix.tobytes()).hexdigest() == row["input"]
    case_path = ROOT / source_protocol["cases_source"]
    assert sha(case_path) == source_protocol["cases_sha256"]
    cases = [row for row in json.loads(case_path.read_text()) if row["split"] == "development"]
    assert len(cases) == 160
    expected = {(row["mapping"], row["input"]): row for row in records(SOURCE / "neural.jsonl.gz")
                if row.get("seed") == SEED and row.get("arm") == "paired" and row["phase"] == "recall"}
    assert len(expected) == 330
    schedules = []
    for epoch in range(8):
        order = list(range(76))
        random.Random(SEED + 260000 + 1000 * epoch).shuffle(order)
        schedules.append(order)
    args.out.mkdir(parents=True, exist_ok=False)
    protocol = {"task": "Development pilot: learned local Place/Defer with fixed score arbitration",
                "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in paths},
                "source": str(SOURCE.relative_to(ROOT)), "source_summary_sha256": sha(SOURCE / "summary.json"),
                "template_protocol": str(template_path.relative_to(ROOT)), "template_protocol_sha256": sha(template_path),
                "cases_sha256": sha(case_path), "graph": graph, "parameters": parameters, "decoder": decoder,
                "seed": SEED, "mappings": [0, 1], "maximum_epochs": 8, "schedules": schedules,
                "training": training, "heldout_evaluated": False,
                "selector": "All empty-cell/digit offers, semantic accepted only, max orientation-corrected score; row-major/digit tie. No legality filter. Stop if none accepted. No Undo executions in this pilot.",
                "teaching": "Existing margin3Hz bidirectional rule; original n3 wrong/timeout-only depression. First epoch with all76 correct and all160 development boards solved without wrong placements. Controls replay selected paired teaching opportunities. No feedback omits DAN; inconsistent balances enabled targets per input, odd extras random.",
                "gates": {"changed_correct": 24, "unchanged_correct": 36, "undo_correct": 16,
                          "solved": 160, "wrong_placements": 0, "contrast_balanced_control_gap": .25},
                "contrast": "Prespecified24 changed ambiguous negatives and4 retained forced positives; balanced accuracy on this28-context task. Full60 and all subgroup counts also reported.",
                "limits": "One inherited history and both mappings, development only. Fixed sensory routing and score selector; local deferral, not learned global planning or calibrated confidence. Every assessed offer counted. Empty input remains unlearned."}
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    (args.out / "cases.json").write_text(json.dumps(cases, indent=2) + "\n")
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    neural_log = gzip.open(args.out / "neural.jsonl.gz", "xt")
    train_log = gzip.open(args.out / "training.jsonl.gz", "xt")
    episode_log = gzip.open(args.out / "episodes.jsonl.gz", "xt")
    weight_checks, results = [], []

    def measure(indices=None, duration=500, pulse=None, learning=False, frozen=True, traced=False):
        brain.weights_frozen = frozen
        before = memory_state(brain)
        stimulation = [] if indices is None else [(indices, parameters["KC_current"])]
        if pulse is not None:
            stimulation.append((circuit[pulse], parameters["DAN_current"]))
        bins = list(range(0, 101, 4)) + list(range(110, 501, 10)) if traced else [0, duration]
        counts, trace = np.zeros(brain.n, dtype=np.int32), []
        for start, end in zip(bins, bins[1:]):
            chunk, _ = brain.step(dark, end - start, stimulation=stimulation, learning=learning, lamina_bias=0)
            counts += chunk
            if traced:
                trace.append({"start_ms": start, "end_ms": end, "selected_KC_counts": chunk[indices].tolist(),
                              "output_counts": {name: chunk[ix].tolist() for name, ix in outputs.items()}})
        hz = {name: float(counts[ix].mean() * 1000 / duration) for name, ix in outputs.items()}
        score = hz["MBON11"] - hz["MBON07"] - decoder["offset_hz"]
        after = memory_state(brain)
        if frozen:
            assert before == after
        return {"duration_ms": duration, "pulse": pulse, "learning": learning, "frozen": frozen,
                "output_hz": hz, "score_hz": score, "action": 1 if score >= decoder["threshold_hz"] else 0 if score <= -decoder["threshold_hz"] else -1,
                "spikes_sha256": hashlib.sha256(counts.tobytes()).hexdigest(), "memory_before": before,
                "memory_after": after, "trace": trace, "KC_spikes": int(counts[circuit["kc"]].sum()),
                "DAN_spikes": {name: int(counts[circuit[name]].sum()) for name in ("reward", "aversive")}}

    def evaluate(context, reference=None):
        full_before = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        responses = {}
        for key, indices in inputs.items():
            brain.reset(keep_memory=True)
            row = measure(indices, traced=True)
            if reference is not None:
                check_measure(row, reference[key], trace=True)
            responses[key] = row
            neural_log.write(json.dumps({**context, "input": key, **row}) + "\n")
        neural_log.flush()
        full_after = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        assert full_before == full_after
        weight_checks.append({**context, "before_sha256": full_before, "after_sha256": full_after})
        return responses

    def score(responses, mapping):
        correct = {"changed": [], "unchanged": [], "undo": [], "forced": []}
        for row in training:
            good = responses[row["input"]]["action"] == (row["label"] ^ mapping)
            group = "undo" if row["operation"] == "undo" else "changed" if row["label"] != row["old_label"] else "unchanged"
            correct[group].append(good)
            if row["operation"] == "place" and row["label"] == 1:
                correct["forced"].append(good)
        return {**{key + "_correct": sum(value) for key, value in correct.items()},
                "contrast_balanced_accuracy": (sum(correct["changed"]) / 24 + sum(correct["forced"]) / 4) / 2,
                "all_judgments_pass": all(all(value) for value in correct.values())}

    def episodes(responses, mapping, context):
        rows = []
        for case in cases:
            episode = play_ranked(case["board"], responses, mapping, encode)
            # Grader metadata enters only after the complete policy trajectory.
            wrong = sum(e["candidate"] != case["solution"][e["target"]] for e in episode["events"])
            row = {**episode, "case_id": case["id"], "stratum": case["stratum"], "blanks": case["blank_count"],
                   "solved": bool(valid_complete(episode["final_board"])), "wrong_placements": wrong}
            episode_log.write(json.dumps({**context, **row}) + "\n")
            rows.append(row)
        episode_log.flush()
        return {"puzzles": len(rows), "solved": sum(r["solved"] for r in rows),
                "wrong_placements": sum(r["wrong_placements"] for r in rows),
                "placements": sum(len(r["events"]) for r in rows),
                "neural_offers": sum(r["neural_offers"] for r in rows),
                "strata": {f"{n}-{s}": {"puzzles": len(sub), "solved": sum(r["solved"] for r in sub)}
                           for n in (2, 3, 4) for s in ("easy", "trap")
                           for sub in [[r for r in rows if r["blanks"] == n and r["stratum"] == s]] if sub}}

    for mapping in (0, 1):
        source_path = SOURCE / f"{SEED}-{mapping}-paired-memory.npz"
        saved = np.load(source_path, allow_pickle=False)
        assert np.array_equal(saved["edge_indices"], circuit["edges"])
        source_run = next(r for r in source_summary["runs"] if (r["seed"], r["mapping"]) == (SEED, mapping))
        brain.reset(keep_memory=False)
        brain.weight[circuit["edges"]], brain.memory_u[:], brain.memory_w[:] = (saved[k] for k in ("weights", "u", "w"))
        assert memory_state(brain) == source_run["arms"]["paired"]["memory"]
        inherited_full = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        inherited = evaluate({"mapping": mapping, "arm": "source", "epoch": 0}, {key: expected[mapping, key] for key in inputs})
        source_sequence = episodes(inherited, mapping, {"mapping": mapping, "arm": "source", "epoch": 0})
        print(json.dumps({"mapping": mapping, "arm": "source", "scores": score(inherited, mapping), "sequence": source_sequence}), flush=True)
        entries, history, arms = [], [], {}
        paired_doses, paired_update_ms = Counter(), 0
        for epoch, order in enumerate(schedules, 1):
            for index in order:
                item = training[index]
                brain.reset(keep_memory=True)
                decision = measure(inputs[item["input"]])
                target = item["label"] ^ mapping
                short = item["operation"] == "place" and item["distinct_peers"] == 3
                teach = decision["action"] != target if short else (1 if target else -1) * decision["score_hz"] < 3
                entry = {"epoch": epoch, "context": index, "input": item["input"], "semantic_target": item["label"], "teach": teach, "short": short}
                entries.append(entry)
                phases = []
                if teach:
                    pulse = "reward" if target else "aversive"
                    phases = [measure(duration=200, pulse=pulse, learning=True, frozen=False), measure(duration=250, frozen=False)]
                    if not short:
                        brain.reset(keep_memory=True)
                        phases += [measure(duration=200, pulse="aversive" if target else "reward"),
                                   measure(inputs[item["input"]], learning=True, frozen=False), measure(duration=250, frozen=False)]
                for phase in phases:
                    if phase["pulse"]:
                        paired_doses[phase["pulse"]] += phase["duration_ms"]
                    if not phase["frozen"]:
                        paired_update_ms += phase["duration_ms"]
                train_log.write(json.dumps({"mapping": mapping, "arm": "paired", **entry, "decision": decision, "phases": phases}) + "\n")
            train_log.flush()
            np.savez_compressed(args.out / f"{mapping}-paired-epoch-{epoch:02d}-memory.npz", edge_indices=circuit["edges"], weights=brain.weight[circuit["edges"]], u=brain.memory_u, w=brain.memory_w)
            responses = evaluate({"mapping": mapping, "arm": "paired", "epoch": epoch})
            scored = score(responses, mapping)
            sequence = episodes(responses, mapping, {"mapping": mapping, "arm": "paired", "epoch": epoch})
            passed = scored["all_judgments_pass"] and sequence["solved"] == 160 and sequence["wrong_placements"] == 0
            history.append({"epoch": epoch, "scores": scored, "sequence": sequence, "pass": passed})
            print(json.dumps({"mapping": mapping, "arm": "paired", **history[-1]}), flush=True)
            (args.out / f"{mapping}-history.json").write_text(json.dumps(history, indent=2) + "\n")
            if passed:
                break
        arms["paired"] = {"scores": scored, "sequence": sequence, "memory": memory_state(brain),
                          "update_window_ms": paired_update_ms, "DAN_pulse_duration_ms": dict(paired_doses)}
        # Balance independent inconsistent targets over enabled occurrences only.
        rng = random.Random(SEED + mapping + 270000)
        for key in inputs:
            selected = [entry for entry in entries if entry["input"] == key and entry["teach"]]
            targets = [i % 2 for i in range(len(selected) // 2 * 2)]
            if len(selected) % 2:
                targets.append(rng.randrange(2))
            rng.shuffle(targets)
            for entry, target in zip(selected, targets):
                entry["inconsistent_target"] = target
        (args.out / f"{mapping}-selected-schedule.json").write_text(json.dumps(entries, indent=2) + "\n")
        # Probe learning erasure and nonplastic integrity before matched controls.
        brain.weight[circuit["edges"]] = brain.baseline_plastic
        assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == original_full
        for arm in ARMS[1:]:
            brain.reset(keep_memory=False)
            brain.weight[circuit["edges"]], brain.memory_u[:], brain.memory_w[:] = (saved[k] for k in ("weights", "u", "w"))
            assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == inherited_full
            if arm == "frozen":
                evaluate({"mapping": mapping, "arm": "erased", "epoch": epoch}, inherited)
            doses, update_ms = Counter(), 0
            for entry in entries:
                brain.reset(keep_memory=True)
                decision = measure(inputs[entry["input"]])
                phases = []
                if entry["teach"]:
                    semantic = entry["inconsistent_target"] if arm == "inconsistent" else entry["semantic_target"]
                    target = semantic ^ mapping
                    pulse = None if arm == "no_feedback" else "reward" if target else "aversive"
                    phases = [measure(duration=200, pulse=pulse, learning=arm != "frozen", frozen=arm == "frozen"),
                              measure(duration=250, frozen=arm == "frozen")]
                    if not entry["short"]:
                        brain.reset(keep_memory=True)
                        opposite = None if pulse is None else "aversive" if target else "reward"
                        phases += [measure(duration=200, pulse=opposite),
                                   measure(inputs[entry["input"]], learning=arm != "frozen", frozen=arm == "frozen"),
                                   measure(duration=250, frozen=arm == "frozen")]
                for phase in phases:
                    if phase["pulse"]:
                        doses[phase["pulse"]] += phase["duration_ms"]
                    if not phase["frozen"]:
                        update_ms += phase["duration_ms"]
                train_log.write(json.dumps({"mapping": mapping, "arm": arm, **entry, "decision": decision, "phases": phases}) + "\n")
            train_log.flush()
            np.savez_compressed(args.out / f"{mapping}-{arm}-memory.npz", edge_indices=circuit["edges"], weights=brain.weight[circuit["edges"]], u=brain.memory_u, w=brain.memory_w)
            responses = evaluate({"mapping": mapping, "arm": arm, "epoch": epoch}, inherited if arm == "frozen" else None)
            sequence = episodes(responses, mapping, {"mapping": mapping, "arm": arm, "epoch": epoch})
            arms[arm] = {"scores": score(responses, mapping), "sequence": sequence, "memory": memory_state(brain),
                         "update_window_ms": update_ms, "DAN_pulse_duration_ms": dict(doses)}
            assert update_ms == (0 if arm == "frozen" else paired_update_ms)
            if arm == "frozen":
                assert dict(doses) == dict(paired_doses)
            brain.weight[circuit["edges"]] = brain.baseline_plastic
            assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == original_full
            print(json.dumps({"mapping": mapping, "arm": arm, "scores": arms[arm]["scores"], "sequence": sequence}), flush=True)
        gaps = {arm: arms["paired"]["scores"]["contrast_balanced_accuracy"] - arms[arm]["scores"]["contrast_balanced_accuracy"] for arm in ARMS[1:]}
        results.append({"mapping": mapping, "selected_epoch": epoch if passed else None, "attempted_epochs": epoch,
                        "history": history, "source_sequence": source_sequence, "arms": arms,
                        "control_gaps": gaps, "erasure_exact": True, "nonplastic_unchanged": True,
                        "pilot_gate": passed and min(gaps.values()) >= .25})
        (args.out / "partial-results.json").write_text(json.dumps(results, indent=2) + "\n")
        saved.close()
    neural_log.close()
    train_log.close()
    episode_log.close()
    (args.out / "full-weight-checks.json").write_text(json.dumps(weight_checks, indent=2) + "\n")
    summary = {"pilot_gate": all(r["pilot_gate"] for r in results), "stage6_complete": False,
               "heldout_evaluated": False, "source_summary_sha256": sha(SOURCE / "summary.json"),
               "runs": results, "elapsed_seconds": time.perf_counter() - started,
               "files_sha256": {p.name: sha(p) for p in sorted(args.out.iterdir()) if p.is_file()}}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"pilot_gate": summary["pilot_gate"], "elapsed_seconds": summary["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
