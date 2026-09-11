"""One-blank 4x4 Sudoku using learning inside existing fly synapses.

The grader owns solutions; the encoder receives only rendered masked boards.
"""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from compare_symbols import patch_pixels
from sudokufly import ROOT, UPSTREAM, UPSTREAM_COMMIT, memory_state


def sudoku_orbit_key(cells):
    """Canonicalize all valid geometric symmetries and digit relabelings."""
    orders = tuple(
        tuple(2 * bands[0] + x for x in first)
        + tuple(2 * bands[1] + x for x in second)
        for bands in ((0, 1), (1, 0))
        for first in ((0, 1), (1, 0))
        for second in ((0, 1), (1, 0))
    )
    forms = []
    for transpose, rows, columns in itertools.product((False, True), orders, orders):
        transformed = tuple(
            cells[4 * columns[c] + rows[r]] if transpose
            else cells[4 * rows[r] + columns[c]]
            for r in range(4) for c in range(4)
        )
        # A valid complete first row contains every digit exactly once. Mapping
        # it to 1,2,3,4 removes all 24 possible global digit renamings.
        rename = {digit: i + 1 for i, digit in enumerate(transformed[:4])}
        forms.append(tuple(rename[digit] for digit in transformed))
    canonical = min(forms)
    return "/".join("".join(map(str, canonical[i:i + 4])) for i in range(0, 16, 4))


def enumerate_sudoku_dataset():
    """Return sorted grids, a unique-completion index, and protocol metadata.

    Grids have zero-based stable IDs, flat row-major cells, a symmetry-orbit
    key, and a development/heldout split. The index maps a flat partial grid
    containing one zero to its unique complete grid ID. All blank positions and
    all four candidate digits belong to evaluation; no candidates are filtered.
    """
    permutations = tuple(itertools.permutations((1, 2, 3, 4)))
    solutions = []
    for rows in itertools.product(permutations, repeat=4):
        if any(len({rows[r][c] for r in range(4)}) != 4 for c in range(4)):
            continue
        if any(
            len({rows[r][c] for r in (br, br + 1) for c in (bc, bc + 1)}) != 4
            for br in (0, 2) for bc in (0, 2)
        ):
            continue
        solutions.append(tuple(digit for row in rows for digit in row))
    solutions.sort()
    assert len(solutions) == len(set(solutions)) == 288

    orbit_members = defaultdict(list)
    for cells in solutions:
        orbit_members[sudoku_orbit_key(cells)].append(cells)
    assert sorted(map(len, orbit_members.values())) == [96, 192]
    split_by_orbit = {
        key: "development" if len(members) == 96 else "heldout"
        for key, members in orbit_members.items()
    }
    grids = []
    completions = defaultdict(list)
    for i, cells in enumerate(solutions):
        key = sudoku_orbit_key(cells)
        grid = {"id": f"grid-{i:03d}", "cells": cells,
                "orbit_key": key, "split": split_by_orbit[key]}
        grids.append(grid)
        for blank in range(16):
            partial = cells[:blank] + (0,) + cells[blank + 1:]
            completions[partial].append(grid["id"])
    assert len(completions) == 4608
    assert all(len(ids) == 1 for ids in completions.values())
    completion_index = {partial: ids[0] for partial, ids in completions.items()}

    protocol = {
        "grid_count": len(grids),
        "grid_id_order": "Zero-based grid-NNN IDs in lexicographic row-major digit order.",
        "digit_values": [1, 2, 3, 4],
        "blank_positions": list(range(16)),
        "blank_position_order": "Zero-based row-major; row=position//4, column=position%4.",
        "candidate_values": [1, 2, 3, 4],
        "symmetries": "All digit relabelings; rows within bands; bands; columns within stacks; stacks; transpose.",
        "orbit_key": "Lexicographically smallest transformed grid after first-row digit normalization, with slash-separated rows.",
        "orbits": [
            {"key": key, "grid_count": len(orbit_members[key]),
             "split": split_by_orbit[key]}
            for key in sorted(orbit_members)
        ],
        "unique_completion_verification": "Index every single-position mask of every valid complete grid; each partial grid has exactly one indexed completion.",
        "unique_partial_grids": len(completion_index),
        "candidate_judgments": len(completion_index) * 4,
        "accept_judgments": len(completion_index),
        "reject_judgments": len(completion_index) * 3,
        "development": {"grids": 96, "partial_grids": 1536, "candidate_judgments": 6144},
        "heldout": {"grids": 192, "partial_grids": 3072, "candidate_judgments": 12288},
        "scope": "One-blank missing-symbol judgments. Row-only, column-only, box-only, and global-count shortcuts cannot be separated by this domain.",
    }
    return grids, completion_index, protocol


CELL = 64
BOARD_LEFT = BOARD_TOP = 16
CANDIDATE_LEFT, CANDIDATE_TOP = 304, 112
INNER = 8


def render_board(board, candidate, view="base"):
    """Render a 4x4 integer board; zero denotes the sole blank, digits are 1..4.

    Views change glyph position or size within the fixed cell layout. They do
    not move the grid. The renderer receives no solution, target label, or score.
    """
    board = np.asarray(board)
    if board.shape != (4, 4) or np.count_nonzero(board == 0) != 1:
        raise ValueError("Expected a 4x4 board with exactly one zero blank")
    if not np.isin(board, range(5)).all() or candidate not in (1, 2, 3, 4):
        raise ValueError("Board digits and candidate must use the alphabet 1..4")
    if view not in ("base", "shift", "small"):
        raise ValueError("Expected base, shift, or small view")
    image = Image.new("RGB", (384, 288), "white")
    draw = ImageDraw.Draw(image)
    blank_row, blank_col = np.argwhere(board == 0)[0]
    left = BOARD_LEFT + int(blank_col) * CELL
    top = BOARD_TOP + int(blank_row) * CELL
    draw.rectangle((left + 4, top + 4, left + 60, top + 60),
                   fill=(255, 248, 214), outline=(231, 163, 34), width=3)
    for edge in range(5):
        width = 4 if edge % 2 == 0 else 1
        x, y = BOARD_LEFT + edge * CELL, BOARD_TOP + edge * CELL
        draw.line((x, BOARD_TOP, x, BOARD_TOP + 4 * CELL), fill=(48, 48, 48), width=width)
        draw.line((BOARD_LEFT, y, BOARD_LEFT + 4 * CELL, y), fill=(48, 48, 48), width=width)
    draw.rectangle((CANDIDATE_LEFT, CANDIDATE_TOP,
                    CANDIDATE_LEFT + CELL, CANDIDATE_TOP + CELL),
                   outline=(48, 48, 48), width=2)
    draw.text((CANDIDATE_LEFT - 4, CANDIDATE_TOP - 24), "Candidate",
              fill=(48, 48, 48), font=ImageFont.load_default(size=15))
    font = ImageFont.load_default(size=28 if view == "small" else 32)
    cells = [(BOARD_LEFT + col * CELL, BOARD_TOP + row * CELL, int(board[row, col]))
             for row in range(4) for col in range(4)]
    cells.append((CANDIDATE_LEFT, CANDIDATE_TOP, int(candidate)))
    for left, top, digit in cells:
        if digit == 0:
            continue
        text = str(digit)
        box = draw.textbbox((0, 0), text, font=font)
        x = left + (CELL - (box[2] - box[0])) // 2 - box[0]
        y = top + (CELL - (box[3] - box[1])) // 2 - box[1]
        if view == "shift":
            x += 3
            y -= 2
        draw.text((x, y), text, fill="black", font=font)
    return np.asarray(image)


def encode_board(frame, templates, groups, per_pair=8):
    """Locate the blank from pixels and route its three row peers to KCs.

    The fixed crop/layout and target-row attention are engineered. Grid and
    highlight borders lie outside every crop. `templates` has shape (2,4,64),
    using Step 2's independently permuted candidate/row roles. `groups` has
    shape (16,2,8); use a fixed equal number per hemisphere and constituent pair.
    No template equality test, candidate filtering, or solver runs.
    """
    pixels = []
    for row in range(4):
        for col in range(4):
            top, left = BOARD_TOP + row * CELL, BOARD_LEFT + col * CELL
            pixels.append(patch_pixels(frame[top + INNER:top + CELL - INNER,
                                             left + INNER:left + CELL - INNER]))
    blanks = [i for i, patch in enumerate(pixels) if not np.any(patch)]
    if len(blanks) != 1:
        raise ValueError("Image must contain exactly one empty board-cell interior")
    blank = blanks[0]
    candidate_pixels = patch_pixels(frame[CANDIDATE_TOP + INNER:CANDIDATE_TOP + CELL - INNER,
                                         CANDIDATE_LEFT + INNER:CANDIDATE_LEFT + CELL - INNER])
    candidate = int(np.argmin(np.linalg.norm(templates[0] - candidate_pixels, axis=1)))
    codes = []
    for cell in range((blank // 4) * 4, (blank // 4 + 1) * 4):
        if cell != blank:
            peer = int(np.argmin(np.linalg.norm(templates[1] - pixels[cell], axis=1)))
            codes.append(candidate * len(templates[1]) + peer)
    indices = np.sort(np.concatenate([groups[code, :, :per_pair // 2].ravel() for code in codes]))
    return indices, {"blank_position": [blank // 4, blank % 4], "pair_codes": codes}


def classification_metrics(labels, actions):
    """Timeouts are incorrect, and the 3:1 class imbalance is explicit."""
    correct = labels == actions
    recalls = {str(label): float(correct[labels == label].mean()) for label in (0, 1)}
    accepted = actions == 1
    return {"accuracy": float(correct.mean()),
            "balanced_accuracy": float(np.mean(list(recalls.values()))),
            "class_recall": recalls,
            "precision": float(labels[accepted].mean()) if accepted.any() else 0.0,
            "timeouts": int(np.count_nonzero(actions == -1)), "presentations": len(labels)}


def valid_complete(cells):
    """Independent outcome grader; never used for neural input or selection."""
    grid = np.asarray(cells).reshape(4, 4)
    digits = {1, 2, 3, 4}
    return (all(set(row) == digits for row in grid)
            and all(set(col) == digits for col in grid.T)
            and all(set(grid[r:r + 2, c:c + 2].ravel()) == digits
                    for r in (0, 2) for c in (0, 2)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("development", "heldout", "all"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-pair", type=int, choices=(4, 6, 8), default=8)
    parser.add_argument("--timing", choices=("simultaneous", "staggered"), default="simultaneous")
    parser.add_argument("--mbon-current", type=float)
    parser.add_argument("--train-epochs", type=int, default=0)
    parser.add_argument("--teaching", choices=("bidirectional", "depression"), default="bidirectional")
    parser.add_argument("--conditioning-source", type=Path)
    parser.add_argument("--memory-source", type=Path,
                        default=ROOT / "experiments/level-02/005-controlled-replication/train")
    args = parser.parse_args()
    if args.train_epochs < 0 or (args.train_epochs and
            (args.split != "development" or args.timing != "simultaneous" or args.conditioning_source)):
        parser.error("Conditioning uses development boards, simultaneous inputs, and no conditioned source")
    source = args.memory_source.resolve()
    prior = json.loads((source / "summary.json").read_text())
    source_protocol = json.loads((source / "protocol.json").read_text())
    conditioned = None
    if args.conditioning_source:
        args.conditioning_source = args.conditioning_source.resolve()
        conditioned = json.loads((args.conditioning_source / "summary.json").read_text())
        cp = json.loads((args.conditioning_source / "protocol.json").read_text())
        if not conditioned["gate_passed"] or not cp["training_epochs"] or cp["split"] != "development":
            raise RuntimeError("Confirmation requires passing development conditioning")
        for name, digest in conditioned["files_sha256"].items():
            if hashlib.sha256((args.conditioning_source / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError(f"Conditioned artifact changed: {name}")
    if not prior["gate_passed"]:
        raise RuntimeError("Transfer requires a completed, passing source experiment")
    for name, digest in prior["files_sha256"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Source artifact changed: {name}")
    upstream = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    if upstream != UPSTREAM_COMMIT or dirty:
        raise RuntimeError("Upstream must remain clean and pinned")
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    grids, completion_index, dataset = enumerate_sudoku_dataset()
    selected = [g for g in grids if args.split == "all" or g["split"] == args.split]
    grid_by_id = {g["id"]: g for g in grids}
    (args.out / "grids.json").write_text(json.dumps(grids, indent=2) + "\n")
    os.environ["STONKFLY_DATA"] = str(ROOT / "data")
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.brain import MemoryBrain
    from stonkfly.neural.common import annotations

    graph = verify()
    parameters = source_protocol["parameters"]
    mbon_current = parameters["mbon_current"] if args.mbon_current is None else args.mbon_current
    if not np.isfinite(mbon_current) or mbon_current <= 0:
        raise ValueError("Positive finite output current required")
    brain = MemoryBrain(eta=parameters["eta"])
    c = brain.circuit
    annotation = annotations(brain.ids)
    outputs = {name: np.flatnonzero(annotation.type.eq(name)) for name in ("MBON07", "MBON11")}
    for indices in outputs.values():
        brain.tonic[indices] = mbon_current
    initial_hash = hashlib.sha256(brain.weight.tobytes()).hexdigest()
    if initial_hash != source_protocol["initial_weights_sha256"]:
        raise RuntimeError("Graph initial weights differ from trained source")
    positions = {int(cell): i for i, cell in enumerate(brain.ids)}
    groups = np.array([positions[int(cell)] for cell in np.array(source_protocol["group_KC_ids"]).ravel()],
                      dtype=np.int32).reshape(16, 2, 8)
    templates = np.array(source_protocol["templates"], dtype=np.float64)
    offset = source_protocol["decoder"]["offset_hz"]
    threshold = source_protocol["decoder"]["threshold_hz"]
    if conditioned and (cp["sensory_KCs_per_pair"] != args.per_pair or cp["timing"] != args.timing
                        or cp["inference_mbon_current"] != mbon_current
                        or cp["memory_summary_sha256"] != hashlib.sha256((source / "summary.json").read_bytes()).hexdigest()
                        or cp["decoder"] != {"offset_hz": offset, "threshold_hz": threshold}):
        raise RuntimeError("Confirmation parameters differ from frozen conditioning protocol")
    if conditioned and any(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
                           for name, digest in cp["source_sha256"].items()):
        raise RuntimeError("Confirmation code differs from frozen conditioning source")
    inputs, presentations = {}, []
    views = ("base", "shift", "small")
    with (args.out / "presentations.jsonl").open("x") as manifest:
        for grid in selected:
            for blank in range(16):
                board = np.array(grid["cells"]).reshape(4, 4).copy()
                board.ravel()[blank] = 0
                if completion_index[tuple(board.ravel())] != grid["id"]:
                    raise RuntimeError("Masked board completion mismatch")
                for view in views:
                    for candidate in (1, 2, 3, 4):
                        frame = render_board(board, candidate, view)
                        indices, diagnostic = encode_board(frame, templates, groups, args.per_pair)
                        if diagnostic["blank_position"] != [blank // 4, blank % 4]:
                            raise RuntimeError("Pixel-derived blank position is incorrect")
                        if len(indices) != 3 * args.per_pair or len(np.unique(indices)) != 3 * args.per_pair:
                            raise RuntimeError("Unexpected number of distinct existing sensory KCs")
                        key = hashlib.sha256(indices.tobytes()).hexdigest()
                        inputs.setdefault(key, indices)
                        row = {"grid_id": grid["id"], "blank": blank, "candidate": candidate,
                               "view": view, "label": int(candidate == grid["cells"][blank]),
                               "image_sha256": hashlib.sha256(frame.tobytes()).hexdigest(), "input": key}
                        manifest.write(json.dumps(row) + "\n")
                        presentations.append(row)
                        if grid["id"] == selected[0]["id"] and blank in (0, 5) and candidate in (1, 2):
                            Image.fromarray(frame).save(args.out / f"example-{blank}-{candidate}-{view}.png")
    (args.out / "inputs.json").write_text(json.dumps(
        {key: {"KC_ids": brain.ids[ix].tolist()} for key, ix in inputs.items()}, indent=2) + "\n")
    for key in inputs:
        if len({r["label"] for r in presentations if r["input"] == key}) != 1:
            raise RuntimeError("Conflicting labels share one neural input")
    protocol = {
        "task": "Step3: one-blank4x4 Sudoku candidate transfer", "split": args.split,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                          for name in ("one_blank.py", "compare_symbols.py", "sudokufly.py")},
        "upstream": upstream, "graph": graph, "initial_weights_sha256": initial_hash,
        "memory_source": str(source.relative_to(ROOT)),
        "memory_summary_sha256": hashlib.sha256((source / "summary.json").read_bytes()).hexdigest(),
        "memory_protocol_sha256": hashlib.sha256((source / "protocol.json").read_bytes()).hexdigest(),
        "source_parameters": parameters, "decoder": {"offset_hz": offset, "threshold_hz": threshold},
        "inference_mbon_current": mbon_current,
        "training_epochs": args.train_epochs,
        "teaching": args.teaching,
        "conditioning_source": str(args.conditioning_source.relative_to(ROOT)) if conditioned else None,
        "conditioning_summary_sha256": hashlib.sha256((args.conditioning_source / "summary.json").read_bytes()).hexdigest() if conditioned else None,
        "conditioning": "When enabled, every arm starts from the same paired Step2 memory. Balanced 24-trial epochs use the 16 development inputs: each accept input 3 times, reject once. Paired teaches only wrong/time-out decisions using the unchanged local rule. Depression: cue500, target DAN200 learning, passive250ms. Bidirectional additionally resets electrical state, gives opposite DAN200 frozen, same cue500 learning, passive250ms. Frozen/no-feedback replay the teaching schedule. Inconsistent permutes teaching/no-teaching events across the same cue schedule, preserving dose but changing active windows. Correct/no-teaching trials remain frozen. Stage erasure restores inherited weights and latent memory. No training on heldout boards.",
        "sensory_KCs_per_pair": args.per_pair, "total_sensory_KCs": 3 * args.per_pair,
        "timing": args.timing,
        "onsets_ms": "Simultaneous: all zero. Staggered: 4*(SHA256(decimal neuron ID).first_byte % 8); current stays on from onset to 500ms. Fixed per-neuron delays, no direct symbol or label lookup; exposure472-500ms.",
        "dataset": dataset, "selected_grids": [g["id"] for g in selected], "views": views,
        "rendered_presentations": len(presentations), "distinct_neural_inputs": len(inputs),
        "encoding": "Full masked board pixels plus candidate. Fixed cell crops locate sole blank; fixed target-row attention and existing template banks route three independent candidate/peer pairs. Each pair gets the same preset number of representatives, equally divided between hemispheres, from the saved Step2 group ordering. No solution, equality, legal-candidate flag or label enters encoder. Off-row information is intentionally excluded after blank detection.",
        "inference": "500ms from reset, all memory updates and passive relaxation frozen, retinal and lamina drive zero. KC current and readout unchanged. Uniform output current and timing are explicitly recorded. No dopamine teaching during inference; any separate development conditioning is explicitly recorded.",
        "scan": "Replay candidates1,2,3,4 in that fixed order using the frozen responses; place first semantically accepted digit without filtering, retries or oracle correction. Grade the resulting complete board afterward.",
        "gates": {"balanced_accuracy": .90, "minimum_class_recall": .85,
                  "minimum_group_balanced_accuracy": .85, "minimum_precision": .90,
                  "minimum_completion_rate": .90, "minimum_control_gain": .25,
                  "exact_erasure": True, "nonplastic_preservation": True},
        "limits": "Four familiar symbols, one blank in a valid board. Template recognition and target-row attention/pooling engineered. Row/column/box/global-count shortcuts cannot be distinguished. Many boards/views alias the same16 neural inputs, including across structural splits. Conditioning, when enabled, sees all16 representations. This is not general Sudoku solving or an independent neural generalization test.",
    }
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    print(json.dumps({"environment_ready": True, "grids": len(selected),
                      "presentations": len(presentations), "neural_inputs": len(inputs)}), flush=True)
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    log = (args.out / "neural.jsonl").open("x")
    measured = 0
    training_log = (args.out / "training.jsonl").open("x") if args.train_epochs else None

    def training_segment(indices=None, duration=500, pulse=None, learning=False, frozen=True):
        brain.weights_frozen = frozen
        before = memory_state(brain)
        stimulation = [] if indices is None else [(indices, parameters["kc_current"])]
        if pulse is not None:
            stimulation.append((c[pulse], 20))
        counts, _ = brain.step(dark, duration, stimulation=stimulation, learning=learning, lamina_bias=0)
        hz = {name: float(counts[ix].mean() * 1000 / duration) for name, ix in outputs.items()}
        score = hz["MBON11"] - hz["MBON07"] - offset
        after = memory_state(brain)
        if frozen and before != after:
            raise RuntimeError("Frozen conditioning phase changed memory")
        return {"duration_ms": duration, "pulse": pulse, "learning": learning, "frozen": frozen,
                "score_hz": score, "action": 1 if score >= threshold else 0 if score <= -threshold else -1,
                "spikes_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
                "KC_spikes": int(counts[c["kc"]].sum()),
                "selected_KC_spikes": int(counts[indices].sum()) if indices is not None else 0,
                "DAN_spikes": {p: int(counts[c[p]].sum()) for p in ("reward", "aversive")},
                "memory_before": before, "memory_after": after}

    def evaluate_neural(context):
        nonlocal measured
        responses = {}
        for key, indices in inputs.items():
            brain.reset(keep_memory=True)
            brain.weights_frozen = True
            before = memory_state(brain)
            onsets = np.array([4 * (hashlib.sha256(str(int(brain.ids[ix])).encode()).digest()[0] % 8)
                               if args.timing == "staggered" else 0 for ix in indices])
            counts = np.zeros(brain.n, dtype=np.int32)
            trace = []
            # Record 4ms bins for the first 100ms, then 10ms bins. The same
            # boundaries apply to both timing conditions; sum before decoding.
            boundaries = list(range(0, 101, 4)) + list(range(110, 501, 10))
            for start, end in zip(boundaries, boundaries[1:]):
                active = indices[onsets <= start]
                chunk, _ = brain.step(dark, end - start,
                                      stimulation=[(active, parameters["kc_current"])],
                                      learning=False, lamina_bias=0)
                counts += chunk
                trace.append({"start_ms": start, "end_ms": end,
                              "selected_KC_counts": chunk[indices].tolist(),
                              "output_counts": {name: chunk[ix].tolist() for name, ix in outputs.items()}})
            hz = {name: float(counts[ix].mean() * 2) for name, ix in outputs.items()}
            score = hz["MBON11"] - hz["MBON07"] - offset
            after = memory_state(brain)
            if before != after:
                raise RuntimeError("Frozen inference changed effective or latent memory")
            row = {**context, "input": key, "output_hz": hz, "score_hz": score,
                   "action": 1 if score >= threshold else 0 if score <= -threshold else -1,
                   "spikes_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
                   "selected_KC_spikes": int(counts[indices].sum()),
                   "KC_spikes": int(counts[c["kc"]].sum()),
                   "DAN_spikes": {p: int(counts[c[p]].sum()) for p in ("reward", "aversive")},
                   "memory_before": before, "memory_after": after}
            row.update(onsets_ms=onsets.tolist(), trace=trace)
            log.write(json.dumps(row, allow_nan=False) + "\n")
            log.flush()
            responses[key] = row
            measured += 1
        return responses

    def score_responses(responses, mapping):
        labels = np.array([r["label"] for r in presentations])
        actions = np.array([responses[r["input"]]["action"] for r in presentations])
        if mapping:
            actions = np.where(actions == -1, -1, 1 - actions)
        result = classification_metrics(labels, actions)
        for field, values in (("candidate", range(1, 5)), ("blank", range(16)), ("view", views)):
            result["by_" + field] = {str(value): classification_metrics(
                labels[mask := np.array([r[field] == value for r in presentations])], actions[mask])
                for value in values}
        margins = [(1 if r["label"] != mapping else -1) * responses[r["input"]]["score_hz"] - threshold
                   for r in presentations]
        result["minimum_target_margin_hz"] = min(margins)
        grouped = actions.reshape(-1, 4)
        accepted = grouped == 1
        chosen = np.where(accepted.any(axis=1), accepted.argmax(axis=1) + 1, 0)
        solved = 0
        for row, digit in zip(presentations[::4], chosen):
            original = np.array(grid_by_id[row["grid_id"]]["cells"])
            board = original.copy()
            board[row["blank"]] = int(digit)
            givens = np.arange(16) != row["blank"]
            solved += valid_complete(board) and np.array_equal(board[givens], original[givens])
        result["completion"] = {"rendered_boards": len(chosen), "solved": int(solved),
                                "solve_rate": float(solved / len(chosen)),
                                "no_acceptance": int(np.count_nonzero(chosen == 0)),
                                "exactly_one_acceptance_rate": float(np.mean(accepted.sum(axis=1) == 1)),
                                "mean_candidates_examined": float(np.where(chosen == 0, 4, chosen).mean())}
        return result

    brain.reset(keep_memory=False)
    baseline = evaluate_neural({"phase": "baseline"})
    results = []
    references = []
    for source_run in prior["runs"]:
        seed, mapping = source_run["seed"], source_run["mapping"]
        arms = {}
        inherited = None
        if args.train_epochs or conditioned:
            inherited_path = source / f"{seed}-{mapping}-paired-memory.npz"
            with np.load(inherited_path, allow_pickle=False) as saved:
                inherited = {k: saved[k].copy() for k in ("weights", "u", "w")}
            brain.reset(keep_memory=False)
            brain.weight[c["edges"]] = inherited["weights"]
            brain.memory_u[:] = inherited["u"]
            brain.memory_w[:] = inherited["w"]
            inherited_state = memory_state(brain)
            inherited_responses = evaluate_neural({"seed": seed, "mapping": mapping, "phase": "inherited"})
        if args.train_epochs:
            representatives = {key: next(r for r in presentations if r["input"] == key) for key in inputs}
            schedule = []
            for epoch in range(args.train_epochs):
                chunk = [key for key in sorted(inputs) for _ in range(3 if representatives[key]["label"] else 1)]
                random.Random(seed + 1000 + epoch * 100).shuffle(chunk)
                schedule.extend(chunk)
            paired_events = []
        for arm in ("paired", "frozen", "no_feedback", "inconsistent"):
            path = ((args.conditioning_source / f"{seed}-{mapping}-{arm}-memory.npz") if conditioned
                    else source / f"{seed}-{mapping}-{'paired' if args.train_epochs else arm}-memory.npz")
            with np.load(path, allow_pickle=False) as saved:
                if not np.array_equal(saved["edge_indices"], c["edges"]):
                    raise RuntimeError("Saved plastic edge selection differs")
                brain.reset(keep_memory=False)
                brain.weight[c["edges"]] = saved["weights"]
                brain.memory_u[:] = saved["u"]
                brain.memory_w[:] = saved["w"]
            state = memory_state(brain)
            expected = (next(r for r in conditioned["runs"] if r["seed"] == seed and r["mapping"] == mapping)["arms"][arm]["memory"]
                        if conditioned else source_run["arms"]["paired" if args.train_epochs else arm]["memory"])
            if state != expected:
                raise RuntimeError("Restored memory differs from trained source")
            if args.train_epochs:
                events = list(paired_events)
                if arm == "inconsistent":
                    random.Random(seed + 2000 + mapping).shuffle(events)
                    if events == paired_events:
                        raise RuntimeError("Inconsistent teaching schedule did not change")
                for trial, key in enumerate(schedule):
                    brain.reset(keep_memory=True)
                    decision = training_segment(inputs[key])
                    target = representatives[key]["label"] ^ mapping
                    if arm == "paired":
                        pulse = ("reward" if target else "aversive") if decision["action"] != target else None
                        paired_events.append(pulse)
                    else:
                        pulse = events[trial]
                    phases = []
                    if pulse is not None:
                        actual = None if arm == "no_feedback" else pulse
                        phases.append(training_segment(duration=200, pulse=actual, learning=arm != "frozen", frozen=arm == "frozen"))
                        phases.append(training_segment(duration=250, frozen=arm == "frozen"))
                        if args.teaching == "bidirectional":
                            brain.reset(keep_memory=True)
                            opposite = None if actual is None else "aversive" if actual == "reward" else "reward"
                            phases.append(training_segment(duration=200, pulse=opposite))
                            phases.append(training_segment(inputs[key], learning=arm != "frozen", frozen=arm == "frozen"))
                            phases.append(training_segment(duration=250, frozen=arm == "frozen"))
                    training_log.write(json.dumps({"seed": seed, "mapping": mapping, "arm": arm,
                        "trial": trial, "input": key, "presentation": representatives[key], "target": target,
                        "scheduled_pulse": pulse, "decision": decision, "phases": phases}) + "\n")
                training_log.flush()
                state = memory_state(brain)
                np.savez_compressed(args.out / f"{seed}-{mapping}-{arm}-memory.npz",
                                    edge_indices=c["edges"], weights=brain.weight[c["edges"]],
                                    u=brain.memory_u, w=brain.memory_w)
            responses = evaluate_neural({"seed": seed, "mapping": mapping, "arm": arm, "phase": "recall"})
            scored = score_responses(responses, mapping)
            stage_changed_edges = int(np.count_nonzero(brain.weight[c["edges"]] != inherited["weights"])) if inherited is not None else None
            if inherited is not None:
                brain.reset(keep_memory=False)
                brain.weight[c["edges"]] = inherited["weights"]
                brain.memory_u[:] = inherited["u"]
                brain.memory_w[:] = inherited["w"]
                if memory_state(brain) != inherited_state:
                    raise RuntimeError("Stage erasure changed inherited memory")
                stage_erased = evaluate_neural({"seed": seed, "mapping": mapping, "arm": arm, "phase": "stage_erased"})
                if any(stage_erased[k]["spikes_sha256"] != inherited_responses[k]["spikes_sha256"] for k in inputs):
                    raise RuntimeError("Stage erasure failed")
                if arm == "frozen" and any(responses[k]["spikes_sha256"] != inherited_responses[k]["spikes_sha256"] for k in inputs):
                    raise RuntimeError("Frozen inherited control changed")
            brain.reset(keep_memory=False)
            if hashlib.sha256(brain.weight.tobytes()).hexdigest() != initial_hash:
                raise RuntimeError("Nonplastic weights changed")
            erased = evaluate_neural({"seed": seed, "mapping": mapping, "arm": arm, "phase": "erased"})
            if any(erased[key]["spikes_sha256"] != baseline[key]["spikes_sha256"] for key in inputs):
                raise RuntimeError("Exact memory erasure failed")
            if inherited is None and arm in ("frozen", "no_feedback") and any(
                    responses[key]["spikes_sha256"] != baseline[key]["spikes_sha256"] for key in inputs):
                raise RuntimeError("Unlearned source control differs from baseline")
            arms[arm] = {"evaluation": scored, "memory": state, "erasure_exact": True,
                         "nonplastic_unchanged": True,
                         "stage_erasure_exact": True if inherited is not None else None,
                         "changed_from_inherited": stage_changed_edges}
            references.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            print(json.dumps({"seed": seed, "mapping": mapping, "arm": arm,
                              "balanced_accuracy": scored["balanced_accuracy"], "raw_accuracy": scored["accuracy"],
                              "completion_rate": scored["completion"]["solve_rate"]}), flush=True)
        paired = arms["paired"]["evaluation"]
        passed = (paired["balanced_accuracy"] >= .90 and min(paired["class_recall"].values()) >= .85
                  and paired["precision"] >= .90 and paired["completion"]["solve_rate"] >= .90
                  and all(group["balanced_accuracy"] >= .85 for field in ("by_candidate", "by_blank", "by_view")
                          for group in paired[field].values())
                  and all(paired["balanced_accuracy"] >= arms[arm]["evaluation"]["balanced_accuracy"] + .25
                          for arm in ("frozen", "no_feedback", "inconsistent")))
        results.append({"seed": seed, "mapping": mapping, "arms": arms, "gate_passed": passed})
        (args.out / "partial-results.json").write_text(json.dumps(results, indent=2) + "\n")
    log.close()
    if training_log:
        training_log.close()
    (args.out / "memory-references.json").write_text(json.dumps(references, indent=2) + "\n")
    summary = {"gate_passed": all(r["gate_passed"] for r in results), "split": args.split,
               "no_new_learning": not bool(args.train_epochs), "runs": results, "measured_neural_evaluations": measured,
               "rendered_presentations": len(presentations), "distinct_neural_inputs": len(inputs),
               "baseline": {str(mapping): score_responses(baseline, mapping) for mapping in (0, 1)},
               "analytic_controls": {"always_reject": {"accuracy": .75, "balanced_accuracy": .5, "completion_rate": 0},
                                     "always_accept": {"accuracy": .25, "balanced_accuracy": .5},
                                     "fair_random_binary_expected": {"accuracy": .5, "balanced_accuracy": .5}},
               "elapsed_seconds": time.perf_counter() - started,
               "files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(args.out.iterdir()) if p.is_file()}}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"complete": str(args.out), "gate_passed": summary["gate_passed"],
                      "seconds": summary["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
