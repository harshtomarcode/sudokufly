"""Step 5 preflight and greedy sequential baseline; undo remains a separate gate.

All candidate decisions come from frozen fly spikes. This baseline never undoes
or filters an accepted placement, and cannot complete the full Step 5 milestone.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image

from compare_symbols import patch_pixels
from constraint_transfer import render_partial
from one_blank import (BOARD_LEFT, BOARD_TOP, CANDIDATE_LEFT, CANDIDATE_TOP,
                       CELL, INNER, classification_metrics, valid_complete, enumerate_sudoku_dataset)
from sudokufly import ROOT, UPSTREAM, UPSTREAM_COMMIT, memory_state

POLICIES = ("eight-per-pair", "capped-24")
SOURCE = ROOT / "experiments/level-03/010-curriculum-continuation/development"
STEP4 = ROOT / "experiments/level-04/001-frozen-transfer/heldout"


def ideal_local_scan(board):
    """Grader-only ascending first-accept scan with perfect immediate legality.

    Visit initial blanks in row-major order, try digits 1,2,3,4, and commit the
    first locally legal candidate. A cell with no accepted candidate stays blank;
    scanning continues. There is no undo and no hidden-solution lookup. A later
    placement can only remove legal candidates, so a cell with no legal candidate
    cannot recover in later sweeps without undo. Returns final board and trace.
    """
    state = list(board)
    trace = []
    for target in range(16):
        if state[target] != 0:
            continue
        peers = [i for i in range(16) if i != target and
                 (i // 4 == target // 4 or i % 4 == target % 4 or
                  (i // 8, i % 4 // 2) == (target // 8, target % 4 // 2))]
        legal = [digit for digit in (1, 2, 3, 4)
                 if all(state[i] != digit for i in peers)]
        choice = legal[0] if legal else 0
        trace.append({"target": target, "legal_candidates": legal,
                      "committed": choice})
        state[target] = choice
    return state, trace


def enumerate_step5_cases(sample_per_stratum=32):
    """Return sampled cases and exact full-domain construction metadata.

    IMPORTANT: solution, stratum, ideal diagnostic, and source family are
    construction/grading metadata, never encoder or runtime-action inputs.
    Puzzles with multiple completions are excluded during construction only.
    Each retained puzzle's sole parent determines development/heldout membership;
    unique completion prevents the same partial board crossing that split.
    """
    if sample_per_stratum <= 0:
        raise ValueError("sample_per_stratum must be positive")
    grids, _, _ = enumerate_sudoku_dataset()
    solutions = np.asarray([grid["cells"] for grid in grids], dtype=np.uint64)
    shifts = 3 * np.arange(16, dtype=np.uint64)
    solution_codes = np.sum(solutions << shifts, axis=1, dtype=np.uint64)
    source_splits = np.asarray([grid["split"] for grid in grids])
    peers = {target: [i for i in range(16) if i != target and
                     (i // 4 == target // 4 or i % 4 == target % 4 or
                      (i // 8, i % 4 // 2) == (target // 8, target % 4 // 2))]
             for target in range(16)}
    hash_prefix = b"sudokufly-step5-board-v1\x00"
    cases, domains = [], {}
    for blank_count in (2, 3, 4):
        masks = list(itertools.combinations(range(16), blank_count))
        keep = np.asarray([((1 << 48) - 1) ^ sum(7 << (3 * i) for i in mask)
                           for mask in masks], dtype=np.uint64)
        # Grid-major order makes first_index // len(masks) the parent solution.
        all_partial = (solution_codes[:, None] & keep[None, :]).ravel()
        codes, first_index, multiplicity = np.unique(
            all_partial, return_index=True, return_counts=True)
        unique = multiplicity == 1
        retained_codes = codes[unique]
        parent = first_index[unique] // len(masks)
        initial = ((retained_codes[:, None] >> shifts) & 7).astype(np.uint8)
        expected = solutions[parent].astype(np.uint8)
        state = initial.copy()
        saw_ambiguity = np.zeros(len(state), dtype=bool)
        saw_deadend = np.zeros(len(state), dtype=bool)
        wrong_commit = np.zeros(len(state), dtype=bool)
        # Vectorized equivalent of ideal_local_scan, used only for exhaustive
        # dataset stratification. Every selected case is checked independently
        # with the straightforward scalar simulator before it is returned.
        for target in range(16):
            indices = np.flatnonzero(state[:, target] == 0)
            if not len(indices):
                continue
            occupied = state[indices[:, None], np.asarray(peers[target])[None, :]]
            legal = np.asarray([(occupied != digit).all(axis=1)
                                for digit in (1, 2, 3, 4)]).T
            counts = legal.sum(axis=1)
            choice = np.argmax(legal, axis=1) + 1
            choice[counts == 0] = 0
            saw_ambiguity[indices] |= counts > 1
            saw_deadend[indices] |= counts == 0
            wrong_commit[indices] |= (choice != 0) & (choice != expected[indices, target])
            state[indices, target] = choice
        solved = (state == expected).all(axis=1)
        # Correct local checking cannot produce a wrong *complete* valid board
        # in this unique-completion domain. Every failure is an actual dead end.
        assert np.array_equal(~solved, saw_deadend)
        assert np.array_equal(~solved, wrong_commit)
        split = source_splits[parent]
        domain = {
            "blank_count": blank_count,
            "mask_count": len(masks),
            "generated_grid_mask_pairs": len(all_partial),
            "distinct_partial_boards": len(codes),
            "unique_completion_puzzles": int(unique.sum()),
            "excluded_multiple_completion_puzzles": int((~unique).sum()),
            "all_distinct_codes_sha256": hashlib.sha256(
                codes.astype("<u8").tobytes()).hexdigest(),
            "unique_codes_sha256": hashlib.sha256(
                retained_codes.astype("<u8").tobytes()).hexdigest(),
            "ideal_local_scan_solved": int(solved.sum()),
            "ideal_local_scan_fraction": float(solved.mean()),
            "ever_locally_ambiguous": int(saw_ambiguity.sum()),
            "wrong_locally_legal_commits": int(wrong_commit.sum()),
            "deadends": int(saw_deadend.sum()),
            "strata": {},
        }
        # The hash contains only the canonical partial board. Neither its
        # solution, output, split, nor desired neural success changes its rank.
        digests = [hashlib.sha256(hash_prefix + int(code).to_bytes(6, "little")).hexdigest()
                   for code in retained_codes]
        for split_name in ("development", "heldout"):
            for stratum in ("easy", "trap"):
                indices = np.flatnonzero((split == split_name) &
                                         (solved if stratum == "easy" else ~solved))
                ranked = sorted(indices.tolist(), key=lambda i: (digests[i], int(retained_codes[i])))
                selected = ranked[:sample_per_stratum]
                domain["strata"][f"{split_name}/{stratum}"] = {
                    "available": len(indices), "sampled": len(selected),
                    "sorted_codes_sha256": hashlib.sha256(
                        retained_codes[indices].astype("<u8").tobytes()).hexdigest(),
                    "selected_hashes_in_rank_order": [digests[i] for i in selected],
                    "selection_cutoff_sha256": digests[selected[-1]] if selected else None,
                }
                for rank, i in enumerate(selected, 1):
                    board, solution = initial[i].tolist(), expected[i].tolist()
                    diagnostic_final, trace = ideal_local_scan(board)
                    assert diagnostic_final == state[i].tolist()
                    assert (diagnostic_final == solution) == bool(solved[i])
                    encoded = int(retained_codes[i])
                    assert encoded == sum(digit << (3 * j) for j, digit in enumerate(board))
                    cases.append({
                        "id": f"b{blank_count}-{digests[i][:16]}",
                        "board": board,
                        "solution": solution,
                        "source_grid_id": grids[int(parent[i])]["id"],
                        "source_orbit_key": grids[int(parent[i])]["orbit_key"],
                        "split": split_name,
                        "blank_count": blank_count,
                        "stratum": stratum,
                        "board_encoding_u48": encoded,
                        "board_sha256": digests[i],
                        "hash_rank_in_stratum": rank,
                        "grader_only_ideal_local_scan": {
                            "solved": bool(solved[i]), "final_board": diagnostic_final,
                            "trace": trace,
                        },
                    })
        domains[str(blank_count)] = domain
    assert len({tuple(case["board"]) for case in cases}) == len(cases)
    metadata = {
        "solution_universe_size": len(grids),
        "source_helper": "one_blank.enumerate_sudoku_dataset",
        "source_grid_family_counts": {
            split: sum(grid["split"] == split for grid in grids)
            for split in ("development", "heldout")},
        "sample_per_existing_stratum": sample_per_stratum,
        "sampled_cases": len(cases),
        "board_encoding": "sum(board[i] << (3*i) for i in range(16)); row-major digits 0..4",
        "hash_sampling": {
            "algorithm": "SHA-256",
            "prefix_hex": hash_prefix.hex(),
            "payload": "prefix bytes followed by board_encoding_u48 as 6 little-endian bytes",
            "selection": "lowest sample_per_stratum lexicographic hexdigests per (blank_count, split, stratum)",
            "tie_break": "ascending board_encoding_u48",
            "universe_digest_format": "ascending compact board codes as consecutive little-endian uint64 values",
            "stratification": "easy iff perfect immediate-legality ascending first-accept completes; trap otherwise",
            "neural_output_used": False,
        },
        "exclusions": "Multiple-completion puzzles excluded in construction only; no inference filtering.",
        "grader_only_fields": ["solution", "source_grid_id", "source_orbit_key", "split",
                               "stratum", "grader_only_ideal_local_scan"],
        "domains": domains,
    }
    return cases, metadata


def encode_sequence(frame, templates, groups, policy):
    """Generic pixel-template routing, with presence pooling of repeated peers.

    Peer identity deduplication never compares a candidate with a peer. Empty
    context deliberately supplies no KC drive; no acceptance is hardcoded.
    """
    patches, highlighted = [], []
    for i in range(16):
        top, left = BOARD_TOP + i // 4 * CELL, BOARD_LEFT + i % 4 * CELL
        patches.append(patch_pixels(frame[top + INNER:top + CELL - INNER,
                                          left + INNER:left + CELL - INNER]))
        if np.array_equal(frame[top + 10, left + 10], (255, 248, 214)):
            highlighted.append(i)
    if len(highlighted) != 1 or np.any(patches[highlighted[0]]):
        raise ValueError("Expected one highlighted empty target")
    target = highlighted[0]
    r, c = divmod(target, 4)
    attended = [i for i in range(16) if i != target and np.any(patches[i]) and
                (i // 4 == r or i % 4 == c or (i // 8, i % 4 // 2) == (r // 2, c // 2))]
    peers = sorted({int(np.argmin(np.linalg.norm(templates[1] - patches[i], axis=1))) for i in attended})
    cp = patch_pixels(frame[CANDIDATE_TOP + INNER:CANDIDATE_TOP + CELL - INNER,
                            CANDIDATE_LEFT + INNER:CANDIDATE_LEFT + CELL - INNER])
    candidate = int(np.argmin(np.linalg.norm(templates[0] - cp, axis=1)))
    per_side = (4 if policy == "eight-per-pair" else min(8, 12 // len(peers))) if peers else 0
    indices = (np.sort(np.concatenate([groups[candidate * 4 + peer, :, :per_side].ravel() for peer in peers]))
               if peers else np.array([], dtype=np.int32))
    assert len(indices) == len(np.unique(indices))
    return indices, {"target": target, "attended": attended, "distinct_peers": len(peers),
                     "peer_templates": peers, "candidate_template": candidate}


def probe_metrics(contexts, actions):
    """The empty and all-four sets have one class; report recalls, not NaNs."""
    labels = np.array([r["label"] for r in contexts])
    actions = np.asarray(actions)
    result = classification_metrics(labels, actions)
    result["by_distinct_peers"] = {}
    for n in range(5):
        mask = np.array([r["distinct_peers"] == n for r in contexts])
        l, a = labels[mask], actions[mask]
        recalls = {str(v): float(np.mean(a[l == v] == v)) for v in (0, 1) if np.any(l == v)}
        result["by_distinct_peers"][str(n)] = {
            "accuracy": float(np.mean(l == a)), "class_recall": recalls,
            "balanced_accuracy": float(np.mean(list(recalls.values()))) if len(recalls) == 2 else None,
            "timeouts": int(np.count_nonzero(a == -1)), "contexts": len(l)}
    nonempty = np.array([r["distinct_peers"] > 0 for r in contexts])
    result["nonempty"] = classification_metrics(labels[nonempty], actions[nonempty])
    return result


def play_greedy(case, responses, templates, groups, policy, mapping):
    """Fixed row-major and ascending digit scan; no grader influences actions.

    An unchanged full sweep is a deterministic stall. No undo is implemented
    in this baseline, which is explicitly ineligible to pass the Step 5 gate.
    """
    board = list(case["board"])
    givens = [i for i, digit in enumerate(board) if digit]
    events = []
    for sweep in range(4):
        changed = False
        for target in range(16):
            if board[target]:
                continue
            for candidate in range(1, 5):
                frame = render_partial(board, target, candidate, "base")
                indices, diagnostic = encode_sequence(frame, templates, groups, policy)
                key = hashlib.sha256(indices.tobytes()).hexdigest()
                raw = responses[key]["action"]
                action = raw if raw == -1 else raw ^ mapping
                before = list(board)
                if action == 1:
                    board[target] = candidate
                    changed = True
                events.append({"sweep": sweep, "target": target, "candidate": candidate,
                               "board_before": before, "board_after": list(board), "input": key,
                               "image_sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
                               "distinct_peers": diagnostic["distinct_peers"], "raw_action": raw, "action": action})
                if action == 1:
                    break
        if all(board) or not changed:
            break
    assert all(board[i] == case["board"][i] for i in givens)
    # Validation happens only after the episode; no repair, retries or filtering.
    return {"case_id": case["id"], "blanks": case["blank_count"], "stratum": case["stratum"],
            "initial_board": case["board"], "final_board": board, "events": events,
            "solved": bool(valid_complete(board)), "filled": all(board),
            "timeouts": sum(e["action"] == -1 for e in events), "undo_count": 0,
            "end": "filled" if all(board) else "stalled" if not changed else "sweep_budget"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    source_summary = json.loads((SOURCE / "summary.json").read_text())
    source_protocol = json.loads((SOURCE / "protocol.json").read_text())
    step4_summary = json.loads((STEP4 / "summary.json").read_text())
    step4_protocol = json.loads((STEP4 / "protocol.json").read_text())
    assert source_summary["gate_passed"] and step4_summary["gate_passed"]
    for directory, summary in ((SOURCE, source_summary), (STEP4, step4_summary)):
        for name, digest in summary["files_sha256"].items():
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest
    upstream = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    assert upstream == UPSTREAM_COMMIT and not dirty
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    # Dataset functions are defined above main; their solution and stratum fields
    # are used only to construct/audit the assay, never by play_greedy.
    cases, dataset = enumerate_step5_cases()
    (args.out / "cases.json").write_text(json.dumps(cases, indent=2) + "\n")
    for blanks, stratum in itertools.product((2, 3, 4), ("easy", "trap")):
        selected = [c for c in cases if c["split"] == "development" and c["blank_count"] == blanks and c["stratum"] == stratum]
        if selected:
            board = selected[0]["board"]
            Image.fromarray(render_partial(board, board.index(0), 1, "base")).save(args.out / f"example-{blanks}-{stratum}.png")
    os.environ["STONKFLY_DATA"] = str(ROOT / "data")
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.brain import MemoryBrain
    from stonkfly.neural.common import annotations

    graph = verify()
    parameters = source_protocol["source_parameters"]
    brain = MemoryBrain(eta=parameters["eta"])
    c = brain.circuit
    annotation = annotations(brain.ids)
    outputs = {name: np.flatnonzero(annotation.type.eq(name)) for name in ("MBON07", "MBON11")}
    for ix in outputs.values():
        brain.tonic[ix] = source_protocol["inference_mbon_current"]
    initial_hash = hashlib.sha256(brain.weight.tobytes()).hexdigest()
    assert initial_hash == source_protocol["initial_weights_sha256"]
    step2 = ROOT / source_protocol["memory_source"]
    sp = json.loads((step2 / "protocol.json").read_text())
    assert hashlib.sha256((step2 / "protocol.json").read_bytes()).hexdigest() == source_protocol["memory_protocol_sha256"]
    positions = {int(cell): i for i, cell in enumerate(brain.ids)}
    groups = np.array([positions[int(cell)] for cell in np.array(sp["group_KC_ids"]).ravel()], dtype=np.int32).reshape(16, 2, 8)
    templates = np.array(sp["templates"], dtype=np.float64)
    offset, threshold = (source_protocol["decoder"][k] for k in ("offset_hz", "threshold_hz"))
    contexts, inputs = [], {}
    for policy in POLICIES:
        for n in range(5):
            for peers in itertools.combinations(range(1, 5), n):
                board = [0] * 16
                for position, digit in zip((1, 2, 4, 5), peers):
                    board[position] = digit
                for candidate in range(1, 5):
                    keys = set()
                    for view in ("base", "shift", "small"):
                        frame = render_partial(board, 0, candidate, view)
                        indices, diagnostic = encode_sequence(frame, templates, groups, policy)
                        key = hashlib.sha256(indices.tobytes()).hexdigest()
                        inputs.setdefault(key, indices)
                        keys.add(key)
                        assert diagnostic["distinct_peers"] == n
                    assert len(keys) == 1
                    contexts.append({"policy": policy, "peers": peers, "candidate": candidate,
                                     "distinct_peers": n, "input": key, "active_KCs": len(indices),
                                     "label": int(candidate not in peers)})
    assert len(contexts) == 128 and len(inputs) == 105
    (args.out / "contexts.json").write_text(json.dumps(contexts, indent=2) + "\n")
    (args.out / "inputs.json").write_text(json.dumps(
        {key: {"KC_ids": brain.ids[ix].tolist()} for key, ix in inputs.items()}, indent=2) + "\n")
    source_files = ("sequence_sudoku.py", "constraint_transfer.py", "one_blank.py", "compare_symbols.py", "sudokufly.py")
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_files}
    assert all(hashes[name] == digest for name, digest in source_protocol["source_sha256"].items())
    assert all(hashes[name] == digest for name, digest in step4_protocol["source_sha256"].items())
    protocol = {
        "task": "Step5 prerequisite: variable-peer frozen probe and greedy sequential baseline",
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": hashes, "upstream": upstream, "graph": graph, "initial_weights_sha256": initial_hash,
        "memory_source": str(SOURCE.relative_to(ROOT)),
        "memory_summary_sha256": hashlib.sha256((SOURCE / "summary.json").read_bytes()).hexdigest(),
        "step4_confirmation_sha256": hashlib.sha256((STEP4 / "summary.json").read_bytes()).hexdigest(),
        "parameters": {"KC_current": parameters["kc_current"], "MBON_current": source_protocol["inference_mbon_current"],
                       "duration_ms": 500, "timing": "simultaneous"},
        "decoder": {"offset_hz": offset, "threshold_hz": threshold}, "training_epochs": 0,
        "policies": {"eight-per-pair": "8 KCs per DISTINCT peer pair, including repeated symbols only once; active0,8,16,24,32.",
                     "capped-24": "min(8,12//n) preset KCs per hemisphere per distinct pair; active0,16,24,24,24. Empty input remains empty."},
        "probe": {"semantic_contexts_per_policy": 64, "unique_physical_inputs": 105,
                  "views": ["base", "shift", "small"], "labels": "Immediate candidate/peer conflict; grader never enters encoder."},
        "dataset": dataset, "sequence_split": "development", "sequence_sweeps": 4,
        "sequence_driver": "Fixed row-major empty cells, digits1..4. Every neural acceptance commits immediately. No grader filtering, correction or backtracking. Stop on full board, unchanged sweep, or4sweeps. Final validity only afterward.",
        "undo_implemented": False,
        "gates": {"nonempty_balanced_accuracy": .90, "minimum_occupancy_class_recall": .85,
                  "minimum_control_gain": .25, "full_stage5_requires_learned_undo_and_recovery": True},
        "limits": "A prerequisite/baseline assay cannot complete Step5. Both input policies are predeclared and both reported. Empty contexts have no dedicated learned percept. No new learning. Template vision, geometric attention and presence pooling are engineered. Puzzle failures and successful easy cases do not demonstrate undo or search."}
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    print(json.dumps({"environment_ready": True, "inputs": len(inputs), "sampled_development_puzzles": sum(c['split']=='development' for c in cases)}), flush=True)
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    log = (args.out / "neural.jsonl").open("x")
    measured = 0
    weight_checks = []
    source_records = [json.loads(line) for line in (SOURCE / "neural.jsonl").read_text().splitlines()]
    source_baseline = {r["input"]: r for r in source_records if r["phase"] == "baseline"}
    source_recall = {(r["seed"], r["mapping"], r["arm"], r["input"]): r
                     for r in source_records if r["phase"] == "recall"}

    def evaluate(context):
        nonlocal measured
        full_before = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        responses = {}
        for key, indices in inputs.items():
            brain.reset(keep_memory=True)
            brain.weights_frozen = True
            before = memory_state(brain)
            counts = np.zeros(brain.n, dtype=np.int32)
            trace = []
            boundaries = list(range(0, 101, 4)) + list(range(110, 501, 10))
            for start, end in zip(boundaries, boundaries[1:]):
                chunk, _ = brain.step(dark, end - start, stimulation=[(indices, parameters["kc_current"])], learning=False, lamina_bias=0)
                counts += chunk
                trace.append({"start_ms": start, "end_ms": end, "selected_KC_counts": chunk[indices].tolist(),
                              "output_counts": {name: chunk[ix].tolist() for name, ix in outputs.items()}})
            hz = {name: float(counts[ix].mean() * 2) for name, ix in outputs.items()}
            score = hz["MBON11"] - hz["MBON07"] - offset
            after = memory_state(brain)
            assert before == after
            row = {**context, "input": key, "output_hz": hz, "score_hz": score,
                   "action": 1 if score >= threshold else 0 if score <= -threshold else -1,
                   "spikes_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
                   "memory_before": before, "memory_after": after, "trace": trace,
                   "KC_spikes": int(counts[c["kc"]].sum()), "DAN_spikes": {name: int(counts[c[name]].sum()) for name in ("reward", "aversive")}}
            if key in source_baseline:
                expected = (source_recall[(context["seed"], context["mapping"], context["arm"], key)]
                            if context["phase"] == "recall" else source_baseline[key])
                assert all(row[field] == expected[field] for field in (
                    "output_hz", "score_hz", "action", "spikes_sha256", "KC_spikes",
                    "DAN_spikes", "memory_before", "memory_after", "trace"))
            log.write(json.dumps(row) + "\n")
            responses[key] = row
            measured += 1
        log.flush()
        full_after = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        assert full_before == full_after
        weight_checks.append({**context, "before_sha256": full_before, "after_sha256": full_after})
        return responses

    brain.reset(keep_memory=False)
    baseline = evaluate({"phase": "baseline"})
    results, references = [], []
    with (args.out / "episodes.jsonl").open("x") as episodes:
        for source_run in source_summary["runs"]:
            seed, mapping = source_run["seed"], source_run["mapping"]
            arms = {}
            for arm in ("paired", "frozen", "no_feedback", "inconsistent"):
                path = SOURCE / f"{seed}-{mapping}-{arm}-memory.npz"
                brain.reset(keep_memory=False)
                with np.load(path, allow_pickle=False) as saved:
                    assert np.array_equal(saved["edge_indices"], c["edges"])
                    brain.weight[c["edges"]] = saved["weights"]
                    brain.memory_u[:] = saved["u"]
                    brain.memory_w[:] = saved["w"]
                state = memory_state(brain)
                assert state == source_run["arms"][arm]["memory"]
                responses = evaluate({"seed": seed, "mapping": mapping, "arm": arm, "phase": "recall"})
                arm_results = {}
                for policy in POLICIES:
                    selected = [r for r in contexts if r["policy"] == policy]
                    actions = [responses[r["input"]]["action"] for r in selected]
                    semantic = [a if a == -1 else a ^ mapping for a in actions]
                    scored = probe_metrics(selected, semantic)
                    completed = []
                    for case in cases:
                        if case["split"] != "development":
                            continue
                        result = play_greedy(case, responses, templates, groups, policy, mapping)
                        episodes.write(json.dumps({"seed": seed, "mapping": mapping, "arm": arm, "policy": policy, **result}) + "\n")
                        completed.append(result)
                    sequence = {f"{blanks}-{stratum}": {"puzzles": len(subset), "solved": sum(r["solved"] for r in subset),
                                "solve_rate": float(np.mean([r["solved"] for r in subset])),
                                "timeouts": sum(r["timeouts"] for r in subset)}
                                for blanks in (2, 3, 4) for stratum in ("easy", "trap")
                                for subset in [[r for r in completed if r["blanks"] == blanks and r["stratum"] == stratum]] if subset}
                    arm_results[policy] = {"probe": scored, "sequence": sequence}
                brain.reset(keep_memory=False)
                assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_hash
                erased = evaluate({"seed": seed, "mapping": mapping, "arm": arm, "phase": "erased"})
                assert all(erased[k][field] == baseline[k][field] for k in inputs for field in ("spikes_sha256", "memory_before", "memory_after", "trace"))
                if arm in ("frozen", "no_feedback"):
                    assert all(responses[k]["spikes_sha256"] == baseline[k]["spikes_sha256"] for k in inputs)
                arms[arm] = {"policies": arm_results, "memory": state, "erasure_exact": True, "nonplastic_unchanged": True}
                references.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
                print(json.dumps({"seed": seed, "mapping": mapping, "arm": arm,
                                  "probe": {p: v["probe"]["nonempty"]["balanced_accuracy"] for p, v in arm_results.items()},
                                  "solves": {p: {k:v['solve_rate'] for k,v in r['sequence'].items()} for p,r in arm_results.items()}}), flush=True)
            policy_gates = {}
            for policy in POLICIES:
                scored = arms["paired"]["policies"][policy]["probe"]
                policy_gates[policy] = (scored["nonempty"]["balanced_accuracy"] >= .90 and
                    all(recall >= .85 for n,v in scored["by_distinct_peers"].items() if n != "0" for recall in v["class_recall"].values()) and
                    all(scored["nonempty"]["balanced_accuracy"] >= arms[a]["policies"][policy]["probe"]["nonempty"]["balanced_accuracy"] + .25
                        for a in ("frozen", "no_feedback", "inconsistent")))
            results.append({"seed": seed, "mapping": mapping, "arms": arms, "nonempty_policy_gates": policy_gates})
            (args.out / "partial-results.json").write_text(json.dumps(results, indent=2) + "\n")
    log.close()
    (args.out / "full-weight-checks.json").write_text(json.dumps(weight_checks, indent=2) + "\n")
    (args.out / "memory-references.json").write_text(json.dumps(references, indent=2) + "\n")
    summary = {"stage5_complete": False, "undo_implemented": False, "no_new_learning": True,
               "policy_gates": {p: all(r["nonempty_policy_gates"][p] for r in results) for p in POLICIES},
               "runs": results, "measured_neural_evaluations": measured, "elapsed_seconds": time.perf_counter() - started,
               "files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.out.iterdir()) if p.is_file()}}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"complete": str(args.out), "stage5_complete": False, "policy_gates": summary["policy_gates"], "seconds": summary["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
