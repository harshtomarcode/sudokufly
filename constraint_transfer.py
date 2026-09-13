"""Step 4: frozen fly-memory transfer to isolated Sudoku constraints.

Template vision and target-unit attention are engineered. No new learning runs.
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
from PIL import Image, ImageDraw, ImageFont

from compare_symbols import patch_pixels
from one_blank import (BOARD_LEFT, BOARD_TOP, CANDIDATE_LEFT, CANDIDATE_TOP,
                       CELL, INNER, classification_metrics, enumerate_sudoku_dataset)
from sudokufly import ROOT, UPSTREAM, UPSTREAM_COMMIT, memory_state

KINDS = ("legal", "row", "column", "box")
VIEWS = ("base", "shift", "small")
SOURCE = ROOT / "experiments/level-03/010-curriculum-continuation/development"
CONFIRMATION = SOURCE.parent / "heldout"


def enumerate_geometries():
    """Split occupied layouts under all Sudoku symmetries, before digit assignment.

    Each layout has one row-only, column-only, box-only, and outside clue.
    Candidate and digit identities never determine the split.
    """
    orders = tuple(tuple(2 * bands[0] + x for x in first)
                   + tuple(2 * bands[1] + x for x in second)
                   for bands in ((0, 1), (1, 0))
                   for first in ((0, 1), (1, 0))
                   for second in ((0, 1), (1, 0)))
    transforms = [tuple(4 * columns[i % 4] + rows[i // 4] if transpose
                        else 4 * rows[i // 4] + columns[i % 4] for i in range(16))
                  for transpose, rows, columns in itertools.product((False, True), orders, orders)]
    geometries = []
    for target in range(16):
        row, col = divmod(target, 4)
        row_only = [4 * row + c for c in range(4) if c // 2 != col // 2]
        column_only = [4 * r + col for r in range(4) if r // 2 != row // 2]
        box_only = 4 * (row ^ 1) + (col ^ 1)
        outside = [i for i in range(16) if i // 4 != row and i % 4 != col
                   and (i // 8, i % 4 // 2) != (row // 2, col // 2)]
        for rp, cp, op in itertools.product(row_only, column_only, outside):
            occupied = (rp, cp, box_only, op)
            orbit = min((t[target], *sorted(t[i] for i in occupied)) for t in transforms)
            geometries.append({"id": f"layout-{len(geometries):03d}", "target": target,
                               "occupied": occupied, "orbit": orbit})
    keys = sorted({g["orbit"] for g in geometries})
    grids, _, _ = enumerate_sudoku_dataset()
    solutions = np.array([g["cells"] for g in grids])
    for g in geometries:
        # All other assignments are bijective digit relabelings of 1,2,3,4.
        count = int(np.all(solutions[:, g["occupied"]] == (1, 2, 3, 4), axis=1).sum())
        g["completions_per_assignment"] = count
        g["split"] = ("excluded" if count == 0 else
                      "development" if g["orbit"] in keys[:2] else "heldout")
    assert len(geometries) == 512
    assert len({(g["target"], tuple(sorted(g["occupied"]))) for g in geometries}) == 512
    assert Counter(g["split"] for g in geometries) == {"development": 256, "heldout": 192, "excluded": 64}
    return geometries, [{"key": list(key), "layouts": sum(g["orbit"] == key for g in geometries),
                         "split": next(g["split"] for g in geometries if g["orbit"] == key),
                         "completions_per_assignment": next(g["completions_per_assignment"] for g in geometries if g["orbit"] == key)}
                        for key in keys]


def grade_candidate(board, target, candidate):
    """Independent immediate-rule grader; no completion or neural input is used."""
    grid = np.asarray(board).reshape(4, 4)
    r, c = divmod(target, 4)
    if grid[r, c] != 0:
        raise ValueError("Target must be empty")
    violations = [name for name, values in (
        ("row", grid[r, :]), ("column", grid[:, c]),
        ("box", grid[2 * (r // 2):2 * (r // 2) + 2, 2 * (c // 2):2 * (c // 2) + 2]))
        if np.any(values == candidate)]
    if len(violations) > 1:
        raise ValueError("This assay requires isolated conflicts")
    return 0 if violations else 1, violations[0] if violations else "legal"


def render_partial(board, target, candidate, view):
    """Render only observation fields, with a visible highlighted empty target."""
    if len(board) != 16 or board[target] != 0 or view not in VIEWS:
        raise ValueError("Invalid partial-board observation")
    image = Image.new("RGB", (384, 288), "white")
    draw = ImageDraw.Draw(image)
    left, top = BOARD_LEFT + target % 4 * CELL, BOARD_TOP + target // 4 * CELL
    draw.rectangle((left + 4, top + 4, left + 60, top + 60),
                   fill=(255, 248, 214), outline=(231, 163, 34), width=3)
    for edge in range(5):
        width = 4 if edge % 2 == 0 else 1
        x, y = BOARD_LEFT + edge * CELL, BOARD_TOP + edge * CELL
        draw.line((x, BOARD_TOP, x, BOARD_TOP + 4 * CELL), fill=(48, 48, 48), width=width)
        draw.line((BOARD_LEFT, y, BOARD_LEFT + 4 * CELL, y), fill=(48, 48, 48), width=width)
    draw.rectangle((CANDIDATE_LEFT, CANDIDATE_TOP, CANDIDATE_LEFT + CELL, CANDIDATE_TOP + CELL),
                   outline=(48, 48, 48), width=2)
    draw.text((CANDIDATE_LEFT - 4, CANDIDATE_TOP - 24), "Candidate",
              fill=(48, 48, 48), font=ImageFont.load_default(size=15))
    font = ImageFont.load_default(size=28 if view == "small" else 32)
    cells = [(BOARD_LEFT + i % 4 * CELL, BOARD_TOP + i // 4 * CELL, digit)
             for i, digit in enumerate(board)]
    cells.append((CANDIDATE_LEFT, CANDIDATE_TOP, candidate))
    for left, top, digit in cells:
        if digit == 0:
            continue
        box = draw.textbbox((0, 0), str(digit), font=font)
        x = left + (CELL - (box[2] - box[0])) // 2 - box[0]
        y = top + (CELL - (box[3] - box[1])) // 2 - box[1]
        draw.text((x + (3 if view == "shift" else 0), y - (2 if view == "shift" else 0)),
                  str(digit), fill="black", font=font)
    return np.asarray(image)


def encode_partial(frame, templates, groups):
    """Pixels only: find highlight and pool the union of its three target units.

    Fixed layout, highlight recognition, templates, and geometric attention are
    supplied by the interface. No equality or candidate-legality computation.
    All seven peer positions are considered once, regardless of unit overlap.
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
    peers = [i for i in range(16) if i != target and
             (i // 4 == r or i % 4 == c or (i // 8, i % 4 // 2) == (r // 2, c // 2))]
    attended = [i for i in peers if np.any(patches[i])]
    cp = patch_pixels(frame[CANDIDATE_TOP + INNER:CANDIDATE_TOP + CELL - INNER,
                            CANDIDATE_LEFT + INNER:CANDIDATE_LEFT + CELL - INNER])
    candidate = int(np.argmin(np.linalg.norm(templates[0] - cp, axis=1)))
    codes = [candidate * 4 + int(np.argmin(np.linalg.norm(templates[1] - patches[i], axis=1)))
             for i in attended]
    if len(peers) != 7 or len(codes) != 3 or len(set(codes)) != 3:
        raise ValueError("This transfer assay requires three distinct occupied peers")
    indices = np.sort(np.concatenate([groups[code, :, :4].ravel() for code in codes]))
    if len(indices) != 24 or len(np.unique(indices)) != 24:
        raise ValueError("Expected 24 distinct sensory KCs")
    return indices, {"target": target, "attended": attended, "pair_codes": codes}


def score_judgments(presentations, actions):
    """Report each constraint recall without class-balancing single-class groups."""
    labels = np.array([r["label"] for r in presentations])
    actions = np.asarray(actions)
    result = classification_metrics(labels, actions)
    result["by_kind"] = {kind: {"recall": float(np.mean(actions[mask] == labels[mask])),
                                "presentations": int(mask.sum())}
                         for kind in KINDS
                         for mask in [np.array([r["kind"] == kind for r in presentations])]}
    for field, values in (("candidate", range(1, 5)), ("target", range(16)), ("view", VIEWS)):
        result["by_" + field] = {str(value): classification_metrics(labels[mask], actions[mask])
                                 for value in values
                                 for mask in [np.array([r[field] == value for r in presentations])]}
    result["matched_pair_success"] = {}
    # The legal candidate appears outside. Swapping it with a given peer makes
    # a same-geometry, same-candidate, same-histogram isolated conflict.
    lookup = {(r["layout"], tuple(r["digits"]), r["candidate"], r["view"]): i
              for i, r in enumerate(presentations)}
    for position, kind in enumerate(("row", "column", "box")):
        pairs = []
        for i, row in enumerate(presentations):
            if row["kind"] != "legal":
                continue
            swapped = list(row["digits"])
            swapped[position], swapped[3] = swapped[3], swapped[position]
            j = lookup[(row["layout"], tuple(swapped), row["candidate"], row["view"])]
            assert presentations[j]["kind"] == kind
            pairs.append(actions[i] == 1 and actions[j] == 0)
        result["matched_pair_success"][kind] = float(np.mean(pairs))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("development", "heldout"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    if (args.split == "heldout") != bool(args.reference):
        parser.error("Heldout requires a passed development --reference; development has none")
    started = time.perf_counter()
    source_summary = json.loads((SOURCE / "summary.json").read_text())
    source_protocol = json.loads((SOURCE / "protocol.json").read_text())
    confirmation = json.loads((CONFIRMATION / "summary.json").read_text())
    assert source_summary["gate_passed"] and confirmation["gate_passed"]
    for directory, summary in ((SOURCE, source_summary), (CONFIRMATION, confirmation)):
        for name, digest in summary["files_sha256"].items():
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError(f"Source artifact changed: {directory / name}")
    source_files = ("constraint_transfer.py", "one_blank.py", "compare_symbols.py", "sudokufly.py")
    source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_files}
    if any(source_hashes[name] != digest for name, digest in source_protocol["source_sha256"].items()):
        raise RuntimeError("The earlier experiment source has changed")
    reference = None
    if args.reference:
        args.reference = args.reference.resolve()
        reference = json.loads((args.reference / "summary.json").read_text())
        rp = json.loads((args.reference / "protocol.json").read_text())
        if not reference["gate_passed"] or rp["split"] != "development" or rp["source_sha256"] != source_hashes:
            raise RuntimeError("Confirmation requires a passing development result with identical code")
        if rp["memory_summary_sha256"] != hashlib.sha256((SOURCE / "summary.json").read_bytes()).hexdigest():
            raise RuntimeError("Confirmation memory source differs")
        for name, digest in reference["files_sha256"].items():
            if hashlib.sha256((args.reference / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError(f"Development artifact changed: {name}")
    upstream = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    if upstream != UPSTREAM_COMMIT or dirty:
        raise RuntimeError("Upstream must remain clean and pinned")
    geometries, orbits = enumerate_geometries()
    selected = [g for g in geometries if g["split"] == args.split]
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "layouts.json").write_text(json.dumps(geometries, indent=2) + "\n")
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
    step2_protocol = json.loads((step2 / "protocol.json").read_text())
    assert hashlib.sha256((step2 / "protocol.json").read_bytes()).hexdigest() == source_protocol["memory_protocol_sha256"]
    positions = {int(cell): i for i, cell in enumerate(brain.ids)}
    groups = np.array([positions[int(cell)] for cell in np.array(step2_protocol["group_KC_ids"]).ravel()],
                      dtype=np.int32).reshape(16, 2, 8)
    templates = np.array(step2_protocol["templates"], dtype=np.float64)
    offset, threshold = (source_protocol["decoder"][k] for k in ("offset_hz", "threshold_hz"))
    inputs, presentations = {}, []
    example_kinds = set()
    with (args.out / "presentations.jsonl").open("x") as manifest:
        for gi, geometry in enumerate(selected):
            for digits in itertools.permutations(range(1, 5)):
                board = [0] * 16
                for location, digit in zip(geometry["occupied"], digits):
                    board[location] = digit
                for view, candidate in itertools.product(VIEWS, range(1, 5)):
                    frame = render_partial(board, geometry["target"], candidate, view)
                    indices, diagnostic = encode_partial(frame, templates, groups)
                    assert diagnostic["target"] == geometry["target"]
                    assert set(diagnostic["attended"]) == set(geometry["occupied"][:3])
                    key = hashlib.sha256(indices.tobytes()).hexdigest()
                    inputs.setdefault(key, indices)
                    label, kind = grade_candidate(board, geometry["target"], candidate)
                    row = {"layout": geometry["id"], "digits": digits, "target": geometry["target"],
                           "candidate": candidate, "view": view, "label": label, "kind": kind,
                           "image_sha256": hashlib.sha256(frame.tobytes()).hexdigest(), "input": key}
                    manifest.write(json.dumps(row) + "\n")
                    presentations.append(row)
                    if (kind, view) not in example_kinds:
                        Image.fromarray(frame).save(args.out / f"example-{kind}-{view}.png")
                        example_kinds.add((kind, view))
            if (gi + 1) % 32 == 0:
                print(json.dumps({"rendered_layouts": gi + 1, "of": len(selected)}), flush=True)
    assert len(inputs) == 16
    assert {key: {"KC_ids": brain.ids[ix].tolist()} for key, ix in inputs.items()} == json.loads((SOURCE / "inputs.json").read_text())
    for key in inputs:
        assert len({r["label"] for r in presentations if r["input"] == key}) == 1
    (args.out / "inputs.json").write_text(json.dumps(
        {key: {"KC_ids": brain.ids[ix].tolist()} for key, ix in inputs.items()}, indent=2) + "\n")
    gates = {"balanced_accuracy": .90, "minimum_kind_recall": .85,
             "minimum_group_balanced_accuracy": .85, "minimum_precision": .90,
             "minimum_matched_pair_success": .85, "minimum_control_gain": .25,
             "exact_full_erasure": True, "frozen_memory": True, "nonplastic_preservation": True}
    protocol = {
        "task": "Step4: assisted isolated row/column/box constraint transfer", "split": args.split,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": source_hashes, "upstream": upstream,
        "graph": {"neurons": graph["neurons"], "directed_edges": graph["directed_edges"], "arrays_verified": True},
        "initial_weights_sha256": initial_hash,
        "memory_source": str(SOURCE.relative_to(ROOT)),
        "memory_summary_sha256": hashlib.sha256((SOURCE / "summary.json").read_bytes()).hexdigest(),
        "source_confirmation_sha256": hashlib.sha256((CONFIRMATION / "summary.json").read_bytes()).hexdigest(),
        "reference": str(args.reference.relative_to(ROOT)) if args.reference else None,
        "reference_summary_sha256": hashlib.sha256((args.reference / "summary.json").read_bytes()).hexdigest() if reference else None,
        "parameters": {"KC_current": parameters["kc_current"], "MBON_current": source_protocol["inference_mbon_current"],
                       "duration_ms": 500, "sensory_KCs": 24, "per_pair": 8, "timing": "simultaneous"},
        "decoder": {"offset_hz": offset, "threshold_hz": threshold}, "training_epochs": 0,
        "control_question": "Frozen transfer of each original Step3 arm's own history; no new Step4 learning.",
        "dataset": {"total_layouts": 512, "eligible_layouts": 448, "excluded_uncompletable_layouts": 64,
                    "selected_layouts": len(selected), "orbits": orbits,
                    "split_rule": "First two sorted geometry orbit keys for development; remaining completable keys heldout. Exclude the zero-completion orbit before evaluation. All digit relabelings/candidates/views stay with geometry.",
                    "all_digit_permutations": 24, "all_candidates": [1, 2, 3, 4], "views": VIEWS,
                    "kind_counts": dict(Counter(r["kind"] for r in presentations)),
                    "labels": "Immediate rule legality, independently graded. Each clue digit occurs once globally. Legal candidate appears only outside target units; conflicts are isolated.",
                    "matching": "Swap outside candidate with one target peer, preserving geometry, candidate and full glyph histogram.",
                    "scope": "Four distinct clues: one row-only, column-only, box-only, and outside. Twelve blanks. Every included board has at least one completion, verified against all288 grids. Labels remain immediate legality. No full-puzzle or unique-completion claim."},
        "encoding": "Pixels only. Fixed highlight detector, templates and union-of-units attention. Three independently routed candidate/peer pairs, eight existing KCs each. No equality or legality flag.",
        "rendered_presentations": len(presentations), "distinct_neural_inputs": len(inputs), "gates": gates,
        "limits": "Spatial relevance is supplied by the interface, not learned by the fly. Same 16 representations as Step3. This is frozen assisted transfer, not new learning, novel neural generalization, variable-occupancy support, or sequential Sudoku solving.",
    }
    if reference and (rp["parameters"] != protocol["parameters"] or rp["decoder"] != protocol["decoder"]
                      or rp["gates"] != gates or rp["dataset"]["orbits"] != orbits):
        raise RuntimeError("Confirmation protocol differs from development")
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    print(json.dumps({"environment_ready": True, "presentations": len(presentations), "inputs": len(inputs)}), flush=True)
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    log = (args.out / "neural.jsonl").open("x")
    measured = 0
    source_records = [json.loads(line) for line in (SOURCE / "neural.jsonl").read_text().splitlines()]
    source_baseline = {r["input"]: r for r in source_records if r["phase"] == "baseline"}
    source_recall = {(r["seed"], r["mapping"], r["arm"], r["input"]): r
                     for r in source_records if r["phase"] == "recall"}

    def evaluate(context):
        nonlocal measured
        responses = {}
        for key, indices in inputs.items():
            brain.reset(keep_memory=True)
            brain.weights_frozen = True
            before = memory_state(brain)
            counts = np.zeros(brain.n, dtype=np.int32)
            trace = []
            boundaries = list(range(0, 101, 4)) + list(range(110, 501, 10))
            for start, end in zip(boundaries, boundaries[1:]):
                chunk, _ = brain.step(dark, end - start, stimulation=[(indices, parameters["kc_current"])],
                                      learning=False, lamina_bias=0)
                counts += chunk
                trace.append({"start_ms": start, "end_ms": end, "selected_KC_counts": chunk[indices].tolist(),
                              "output_counts": {name: chunk[ix].tolist() for name, ix in outputs.items()}})
            hz = {name: float(counts[ix].mean() * 2) for name, ix in outputs.items()}
            score = hz["MBON11"] - hz["MBON07"] - offset
            after = memory_state(brain)
            if before != after:
                raise RuntimeError("Frozen evaluation changed memory")
            row = {**context, "input": key, "output_hz": hz, "score_hz": score,
                   "action": 1 if score >= threshold else 0 if score <= -threshold else -1,
                   "spikes_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
                   "KC_spikes": int(counts[c["kc"]].sum()), "selected_KC_spikes": int(counts[indices].sum()),
                   "DAN_spikes": {name: int(counts[c[name]].sum()) for name in ("reward", "aversive")},
                   "memory_before": before, "memory_after": after, "trace": trace}
            expected = (source_recall[(context["seed"], context["mapping"], context["arm"], key)]
                        if context["phase"] == "recall" else source_baseline[key])
            assert all(row[field] == expected[field] for field in (
                "output_hz", "score_hz", "action", "spikes_sha256", "KC_spikes", "selected_KC_spikes",
                "DAN_spikes", "memory_before", "memory_after", "trace")), "Frozen transfer differs from Step3"
            log.write(json.dumps(row, allow_nan=False) + "\n")
            log.flush()
            responses[key] = row
            measured += 1
        return responses

    brain.reset(keep_memory=False)
    baseline = evaluate({"phase": "baseline"})
    results, references = [], []
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
            actions = [r["action"] if r["action"] == -1 else r["action"] ^ mapping
                       for p in presentations for r in [responses[p["input"]]]]
            scored = score_judgments(presentations, actions)
            scored["minimum_target_margin_hz"] = min(
                (1 if p["label"] != mapping else -1) * responses[p["input"]]["score_hz"] - threshold
                for p in presentations)
            brain.reset(keep_memory=False)
            assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_hash
            erased = evaluate({"seed": seed, "mapping": mapping, "arm": arm, "phase": "erased"})
            assert all(erased[k][field] == baseline[k][field] for k in inputs
                       for field in ("spikes_sha256", "memory_before", "memory_after", "trace"))
            if arm in ("frozen", "no_feedback"):
                assert all(responses[k]["spikes_sha256"] == baseline[k]["spikes_sha256"] for k in inputs)
            arms[arm] = {"evaluation": scored, "memory": state, "erasure_exact": True,
                         "source_recall_exact": True, "nonplastic_unchanged": True}
            references.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            print(json.dumps({"seed": seed, "mapping": mapping, "arm": arm,
                              "balanced_accuracy": scored["balanced_accuracy"],
                              "kind_recall": {k: v["recall"] for k, v in scored["by_kind"].items()}}), flush=True)
        paired = arms["paired"]["evaluation"]
        passed = (paired["balanced_accuracy"] >= gates["balanced_accuracy"]
                  and min(v["recall"] for v in paired["by_kind"].values()) >= gates["minimum_kind_recall"]
                  and paired["precision"] >= gates["minimum_precision"]
                  and min(paired["matched_pair_success"].values()) >= gates["minimum_matched_pair_success"]
                  and all(v["balanced_accuracy"] >= gates["minimum_group_balanced_accuracy"]
                          for field in ("by_candidate", "by_target", "by_view") for v in paired[field].values())
                  and all(paired["balanced_accuracy"] >= arms[a]["evaluation"]["balanced_accuracy"] + gates["minimum_control_gain"]
                          for a in ("frozen", "no_feedback", "inconsistent")))
        results.append({"seed": seed, "mapping": mapping, "arms": arms, "gate_passed": passed})
        (args.out / "partial-results.json").write_text(json.dumps(results, indent=2) + "\n")
    log.close()
    (args.out / "memory-references.json").write_text(json.dumps(references, indent=2) + "\n")
    analytic = {name: score_judgments(presentations, [
        0 if name == "global_duplicate" or p["kind"] == name else 1 for p in presentations])
        for name in ("row", "column", "box", "global_duplicate")}
    analytic["outside_clue"] = score_judgments(presentations, [
        int(p["candidate"] == p["digits"][3]) for p in presentations])
    summary = {"gate_passed": all(r["gate_passed"] for r in results), "split": args.split,
               "no_new_learning": True, "runs": results, "measured_neural_evaluations": measured,
               "rendered_presentations": len(presentations), "distinct_neural_inputs": len(inputs),
               "baseline": {str(mapping): score_judgments(presentations, [
                   baseline[p["input"]]["action"] if baseline[p["input"]]["action"] == -1
                   else baseline[p["input"]]["action"] ^ mapping for p in presentations])
                   for mapping in (0, 1)},
               "analytic_controls": analytic, "elapsed_seconds": time.perf_counter() - started,
               "files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(args.out.iterdir()) if p.is_file()}}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"complete": str(args.out), "gate_passed": summary["gate_passed"],
                      "seconds": summary["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
