"""Learn visible Undo associations through existing fly synapses and replay Sudoku.

The replay response table contains frozen neural decisions for input hashes. No
solution, legality test, or dead-end rule selects a runtime action here.
"""

import argparse
import gzip
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

from compare_symbols import balanced_groups, patch_pixels
from constraint_transfer import render_partial
from one_blank import (BOARD_LEFT, BOARD_TOP, CANDIDATE_LEFT, CANDIDATE_TOP,
                       CELL, INNER, classification_metrics, valid_complete)
from sequence_sudoku import POLICIES, SOURCE, encode_sequence, probe_metrics
from sudokufly import ROOT, UPSTREAM, UPSTREAM_COMMIT, memory_state


# A visible operation token, parsed by matching its pixels. Its appearance is
# independent of peer identities, occupancy, action labels, and answer mapping.
UNDO_MARKER = Image.new("RGB", (CELL, CELL), (226, 237, 255))
marker_draw = ImageDraw.Draw(UNDO_MARKER)
marker_draw.rectangle((0, 0, CELL - 1, CELL - 1), outline=(37, 88, 167), width=2)
marker_font = ImageFont.load_default(size=15)
marker_box = marker_draw.textbbox((0, 0), "UNDO", font=marker_font)
marker_draw.text(((CELL - (marker_box[2] - marker_box[0])) // 2 - marker_box[0],
                  (CELL - (marker_box[3] - marker_box[1])) // 2 - marker_box[1]),
                 "UNDO", font=marker_font, fill=(25, 55, 105))
UNDO_PIXELS = np.asarray(UNDO_MARKER).copy()


def render_undo(board, target, view="base"):
    """Show the actual board, even when the highlighted target is now filled.

    The existing partial renderer requires an empty highlight. Draw that shared
    geometry first and restore the target glyph exactly if occupied. No target
    value is omitted from the returned observation. The Undo marker is fixed
    across views; board glyphs keep the existing base/shift/small augmentation.
    """
    if len(board) != 16 or not 0 <= target < 16 or view not in ("base", "shift", "small"):
        raise ValueError("Invalid Undo observation")
    visible = list(board)
    target_digit = visible[target]
    visible[target] = 0
    image = Image.fromarray(render_partial(visible, target, 1, view))
    draw = ImageDraw.Draw(image)
    if target_digit:
        left, top = BOARD_LEFT + target % 4 * CELL, BOARD_TOP + target // 4 * CELL
        font = ImageFont.load_default(size=28 if view == "small" else 32)
        box = draw.textbbox((0, 0), str(target_digit), font=font)
        x = left + (CELL - (box[2] - box[0])) // 2 - box[0]
        y = top + (CELL - (box[3] - box[1])) // 2 - box[1]
        draw.text((x + (3 if view == "shift" else 0), y - (2 if view == "shift" else 0)),
                  str(target_digit), font=font, fill="black")
    draw.rectangle((CANDIDATE_LEFT - 4, CANDIDATE_TOP - 26,
                    CANDIDATE_LEFT + CELL + 12, CANDIDATE_TOP - 2), fill="white")
    draw.text((CANDIDATE_LEFT - 4, CANDIDATE_TOP - 24), "Action",
              font=ImageFont.load_default(size=15), fill=(48, 48, 48))
    image.paste(UNDO_MARKER, (CANDIDATE_LEFT, CANDIDATE_TOP))
    return np.asarray(image)


def encode_undo(frame, templates, undo_groups):
    """Parse operation/highlight pixels and route generic peer-presence bits.

    The four bit positions are independently permuted peer-template identities.
    Every one of the sixteen possible bit patterns selects its own uniform
    sixteen-KC bank; no equality, all-four, legality, or Undo-needed flag enters
    this function. Repeated symbols contribute the same presence bit once.
    The highlighted target's contents never count as one of its own peers.
    """
    operation = frame[CANDIDATE_TOP:CANDIDATE_TOP + CELL,
                      CANDIDATE_LEFT:CANDIDATE_LEFT + CELL]
    if not np.array_equal(operation, UNDO_PIXELS):
        raise ValueError("Expected the visible UNDO operation marker")
    patches, highlighted = [], []
    for i in range(16):
        top, left = BOARD_TOP + i // 4 * CELL, BOARD_LEFT + i % 4 * CELL
        patches.append(patch_pixels(frame[top + INNER:top + CELL - INNER,
                                          left + INNER:left + CELL - INNER]))
        if np.array_equal(frame[top + 10, left + 10], (255, 248, 214)):
            highlighted.append(i)
    if len(highlighted) != 1:
        raise ValueError("Expected one highlighted target")
    target = highlighted[0]
    attended = [i for i in range(16) if i != target and np.any(patches[i]) and
                (i // 4 == target // 4 or i % 4 == target % 4 or
                 (i // 8, i % 4 // 2) == (target // 8, target % 4 // 2))]
    peer_templates = sorted({int(np.argmin(np.linalg.norm(templates[1] - patches[i], axis=1)))
                             for i in attended})
    presence_code = sum(1 << peer for peer in peer_templates)
    indices = np.sort(np.asarray(undo_groups[presence_code], dtype=np.int32).ravel())
    if len(indices) != 16 or len(np.unique(indices)) != 16:
        raise ValueError("Every Undo presence pattern must route sixteen distinct KCs")
    return indices, {"operation": "undo", "target": target, "attended": attended,
                     "peer_templates": peer_templates, "presence_code": presence_code,
                     "distinct_peers": len(peer_templates)}


def play_with_undo(case, responses, templates, groups, undo_groups, policy, mapping,
                   max_sweeps=16, decision_budget=1024, view="base"):
    """Replay a fixed menu with neural placement and explicit neural Undo.

    At each currently empty row-major target, try digits 1..4 until accepted or
    exhausted, then offer Undo regardless of placement acceptance. Accepted Undo
    pops the most recent nongiven placement. Continue the ordinary target order;
    no branch-specific cursor, tried-candidate memory, legality filter, solver,
    failure-triggered menu, or automatic repair exists. Repeated full states are
    recorded and terminate a deterministic cycle; they never change the menu.
    Completion and hard budgets also stop execution.
    """
    if mapping not in (0, 1) or max_sweeps < 1 or decision_budget < 1:
        raise ValueError("Invalid mapping or episode budget")
    initial = list(case["board"])
    board, stack, events = list(initial), [], []
    given_positions = [i for i, digit in enumerate(initial) if digit]
    undos = repeat_visits = 0
    seen, first_loop = {}, None
    budget_hit = cycle_hit = False
    for sweep in range(max_sweeps):
        signature = (tuple(board), tuple(stack))
        if signature in seen:
            repeat_visits += 1
            if first_loop is None:
                first_loop = {"first_sweep": seen[signature], "repeat_sweep": sweep,
                              "period": sweep - seen[signature]}
            cycle_hit = True
            break
        else:
            seen[signature] = sweep
        for target in range(16):
            if board[target]:
                continue
            for candidate in range(1, 5):
                if len(events) >= decision_budget:
                    budget_hit = True
                    break
                frame = render_partial(board, target, candidate, view)
                indices, diagnostic = encode_sequence(frame, templates, groups, policy)
                key = hashlib.sha256(indices.tobytes()).hexdigest()
                raw = responses[key]["action"]
                if raw not in (-1, 0, 1):
                    raise ValueError("Unexpected neural action")
                action = raw if raw == -1 else raw ^ mapping
                before, stack_before = list(board), [list(item) for item in stack]
                if action == 1:
                    board[target] = candidate
                    stack.append((target, candidate))
                events.append({"sweep": sweep, "op": "place", "target": target,
                               "candidate": candidate, "input": key,
                               "image_sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
                               "board_before": before, "board_after": list(board),
                               "stack_before": stack_before, "stack_after": [list(item) for item in stack],
                               "raw_action": raw, "action": action,
                               "distinct_peers": diagnostic["distinct_peers"],
                               "undos": undos, "undo_executed": False, "popped": None})
                if action == 1:
                    break
            if budget_hit:
                break
            if len(events) >= decision_budget:
                budget_hit = True
                break
            # This unconditional operation offer happens even after a successful
            # placement, so the highlighted target may now contain a digit.
            frame = render_undo(board, target, view)
            indices, diagnostic = encode_undo(frame, templates, undo_groups)
            key = hashlib.sha256(indices.tobytes()).hexdigest()
            raw = responses[key]["action"]
            if raw not in (-1, 0, 1):
                raise ValueError("Unexpected neural action")
            action = raw if raw == -1 else raw ^ mapping
            before, stack_before = list(board), [list(item) for item in stack]
            popped = None
            if action == 1 and stack:
                popped = stack.pop()
                assert board[popped[0]] == popped[1] and initial[popped[0]] == 0
                board[popped[0]] = 0
                undos += 1
            events.append({"sweep": sweep, "op": "undo", "target": target,
                           "candidate": None, "input": key,
                           "image_sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
                           "board_before": before, "board_after": list(board),
                           "stack_before": stack_before, "stack_after": [list(item) for item in stack],
                           "raw_action": raw, "action": action,
                           "presence_code": diagnostic["presence_code"],
                           "distinct_peers": diagnostic["distinct_peers"],
                           "undos": undos, "undo_executed": popped is not None,
                           "popped": list(popped) if popped is not None else None})
            if all(board):
                break
        if budget_hit or all(board):
            break
    assert all(board[i] == initial[i] for i in given_positions)
    # All case metadata below is accessed only after actions are complete.
    return {"case_id": case["id"], "blanks": case["blank_count"], "stratum": case["stratum"],
            "initial_board": initial, "final_board": board, "final_stack": [list(item) for item in stack],
            "events": events, "solved": bool(valid_complete(board)), "filled": all(board),
            "decisions": len(events), "sweeps": sweep if cycle_hit else sweep + 1,
            "timeouts": sum(event["action"] == -1 for event in events), "undo_count": undos,
            "undo_accepts": sum(event["op"] == "undo" and event["action"] == 1 for event in events),
            "repeated_state_visits": repeat_visits, "first_loop": first_loop,
            "end": "filled" if all(board) else "decision_budget" if budget_hit else "repeated_state" if cycle_hit else "sweep_budget"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--paired-only", action="store_true", help="Diagnostic only; control-dependent gates remain unassessed")
    args = parser.parse_args()
    if args.epochs < 2 or args.epochs % 2:
        parser.error("Use a positive even number of epochs for balanced per-pattern controls")
    arm_names = ("paired",) if args.paired_only else ("paired", "frozen", "no_feedback", "inconsistent")
    started = time.perf_counter()
    prior = ROOT / "experiments/level-05/001-variable-peers/development"
    source_summary = json.loads((SOURCE / "summary.json").read_text())
    source_protocol = json.loads((SOURCE / "protocol.json").read_text())
    prior_summary = json.loads((prior / "summary.json").read_text())
    prior_protocol = json.loads((prior / "protocol.json").read_text())
    for directory, summary in ((SOURCE, source_summary), (prior, prior_summary)):
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
    assert hashlib.sha256((step2 / "protocol.json").read_bytes()).hexdigest() == source_protocol["memory_protocol_sha256"]
    sp = json.loads((step2 / "protocol.json").read_text())
    positions = {int(cell): i for i, cell in enumerate(brain.ids)}
    groups = np.array([positions[int(cell)] for cell in np.array(sp["group_KC_ids"]).ravel()], dtype=np.int32).reshape(16, 2, 8)
    templates = np.array(sp["templates"], dtype=np.float64)
    offset, threshold = (source_protocol["decoder"][k] for k in ("offset_hz", "threshold_hz"))
    contacts = np.rint(brain.baseline_plastic / 0.275).astype(np.int64)
    mass = {}
    for name, ix in outputs.items():
        keep = np.isin(brain.post[c["edges"]], ix)
        mass[name] = np.bincount(c["pre"][keep], weights=contacts[keep], minlength=brain.n)
    both = np.flatnonzero((mass["MBON07"] > 0) & (mass["MBON11"] > 0))
    excluded = set(groups.ravel().tolist())
    pool = []
    for side in ("L", "R"):
        choices = [int(i) for i in both if i not in excluded and str(annotation.instance.iloc[i]).endswith("_" + side)]
        choices.sort(key=lambda i: (-min(mass["MBON07"][i], mass["MBON11"][i]),
                                    -(mass["MBON07"][i] + mass["MBON11"][i]), int(brain.ids[i])))
        assert len(choices) >= 128
        pool.extend(choices[:128])
    undo_groups, _, anatomy = balanced_groups(brain, np.array(pool, dtype=np.int32), np.concatenate(list(outputs.values())))
    assert not set(undo_groups.ravel().tolist()) & excluded
    inputs = {key: np.array([positions[int(cell)] for cell in row["KC_ids"]], dtype=np.int32)
              for key, row in json.loads((prior / "inputs.json").read_text()).items()}
    prior_input_keys = set(inputs)
    place_contexts = json.loads((prior / "contexts.json").read_text())
    undo_contexts = []
    for count in range(5):
        for peers in itertools.combinations(range(1, 5), count):
            board = [0] * 16
            for position, digit in zip((1, 2, 4, 5), peers):
                board[position] = digit
            keys = set()
            for view in ("base", "shift", "small"):
                frame = render_undo(board, 0, view)
                indices, diagnostic = encode_undo(frame, templates, undo_groups)
                key = hashlib.sha256(indices.tobytes()).hexdigest()
                keys.add(key)
                inputs.setdefault(key, indices)
            assert len(keys) == 1 and len(indices) == 16
            undo_contexts.append({"peers": list(peers), "pattern": diagnostic["presence_code"],
                                  "input": key, "label": int(count == 4)})
            if count in (0, 3, 4):
                Image.fromarray(frame).save(args.out / f"undo-pattern-{diagnostic['presence_code']:02d}.png")
    assert len(inputs) == 121 and len({r["input"] for r in undo_contexts}) == 16
    assert all(hashlib.sha256(ix.tobytes()).hexdigest() == key for key, ix in inputs.items())
    cases = json.loads((prior / "cases.json").read_text())
    (args.out / "undo-contexts.json").write_text(json.dumps(undo_contexts, indent=2) + "\n")
    (args.out / "inputs.json").write_text(json.dumps({key: {"KC_ids": brain.ids[ix].tolist()} for key, ix in inputs.items()}, indent=2) + "\n")
    schedules = {}
    for seed in (20260919, 20260920):
        schedule = []
        for epoch in range(args.epochs):
            chunk = [i for i, row in enumerate(undo_contexts) for _ in range(15 if row["label"] else 1)]
            random.Random(seed + epoch * 100).shuffle(chunk)
            schedule.extend({"epoch": epoch, "context": i} for i in chunk)
        for i in range(16):
            occurrences = [j for j, row in enumerate(schedule) if row["context"] == i]
            labels = [j % 2 for j in range(len(occurrences))]
            random.Random(seed + i + 50000).shuffle(labels)
            for j, label in zip(occurrences, labels):
                schedule[j]["inconsistent_label"] = label
        assert len(schedule) == 30 * args.epochs
        assert sum(row["inconsistent_label"] for row in schedule) == 15 * args.epochs
        schedules[str(seed)] = schedule
    (args.out / "schedules.json").write_text(json.dumps(schedules, indent=2) + "\n")
    source_files = ("learn_undo.py", "sequence_sudoku.py", "constraint_transfer.py", "one_blank.py", "compare_symbols.py", "sudokufly.py")
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in source_files}
    assert all(hashes[name] == digest for name, digest in prior_protocol["source_sha256"].items())
    protocol = {
        "task": "Step5 learned Undo association with warm-memory controls and sequential recovery",
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": hashes, "upstream": upstream, "graph": graph, "initial_weights_sha256": initial_hash,
        "memory_source": str(SOURCE.relative_to(ROOT)), "memory_summary_sha256": hashlib.sha256((SOURCE / "summary.json").read_bytes()).hexdigest(),
        "prior_assay": str(prior.relative_to(ROOT)), "prior_summary_sha256": hashlib.sha256((prior / "summary.json").read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256((prior / "cases.json").read_bytes()).hexdigest(),
        "parameters": {"KC_current": parameters["kc_current"], "MBON_current": source_protocol["inference_mbon_current"],
                       "eta": parameters["eta"], "duration_ms": 500, "DAN_current": 20},
        "epochs": args.epochs, "trials_per_arm": 30 * args.epochs,
        "nonfrozen_active_seconds_per_arm": 36 * args.epochs,
        "arms": list(arm_names), "controls_evaluated": not args.paired_only,
        "decoder": {"offset_hz": offset, "threshold_hz": threshold},
        "undo_KC_ids": brain.ids[undo_groups].tolist(), "anatomy_partition": anatomy,
        "encoder": "Visible UNDO marker and four template-presence bits from highlighted target peers select one of16 equally sized disjoint KC groups. Anatomical ranking excludes every original sensory KC. No new plastic edges, equality flag, dead-end label, or learned output head. All16 patterns are trained; this is an engineered lookup representation, not learned Boolean composition or novel-pattern generalization.",
        "training": f"{args.epochs} fixed epochs of30 trials: full-peer pattern15 times, each other pattern once. All trials receive bidirectional teaching: cue500 frozen; targetDAN200 learning; passive250; reset retaining memory; oppositeDAN200 frozen; cue500 learning; passive250. No response-dependent stopping. Passive weight decay remains active in nonfrozen training windows, including old placement synapses.",
        "controls": "Every arm starts the SAME paired Step3 memory within its mapping/history. Frozen replays correct pulses with weights frozen. No-feedback removes both pulses but retains learning windows and passive decay. Inconsistent shuffles50/50 labels separately across ALL occurrences of each pattern, not epoch blocks; every pulsed trial still delivers both compartments once.",
        "evaluation": "Frozen121-input evaluation from electrical reset; replayed episodes reuse measured deterministic responses and are not independent neural observations. Full W hash before/after each batch. Stage erasure restores inherited W/u/w, full erasure restores original W/u/w; both remeasure16 Undo and16 familiar placement inputs against reference.",
        "sequence": "Development160 cases, both prior placement policies,16 sweeps and1024 decision limit. Row-major currently empty targets; candidates1..4, commit first accept immediately; ALWAYS offer Undo afterward, including after acceptance. Neural Undo acceptance pops latest nongiven placement. Continue global scan without per-branch cursors, legality filtering or grader access; grading after episode only. Stop a repeated complete board+stack state at a sweep boundary because reset/frozen inference would repeat it forever; no retry or repair.",
        "gates": {"undo_balanced_accuracy": .90, "undo_class_recall": .85, "minimum_warm_control_gain": .25,
                  "familiar_placement_retention_accuracy": 1.0, "sequence_per_stratum_solve_rate": .90,
                  "nonempty_placement_balanced_accuracy": .90, "placement_occupancy_class_recall": .85,
                  "placement_gain_over_original_history_controls": .25},
        "stage5_complete": False,
        "limits": "Development association/recovery experiment only. Failed001 occupancy prerequisites remain reported; no heldout confirmation in this run. Even a successful Undo association cannot complete Step5. Two inherited training histories are deterministic saved states, not independent connectomes. Fixed vision, state routing, scan order and stack mechanics are supplied."}
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    log = (args.out / "neural.jsonl").open("x")
    training_log = (args.out / "training.jsonl").open("x")
    weight_checks, references = [], []
    measured = 0
    familiar = json.loads((SOURCE / "inputs.json").read_text())
    ablation_keys = list(dict.fromkeys([r["input"] for r in undo_contexts] + list(familiar)))
    assert len(ablation_keys) == 32
    prior_responses = {}
    for line in (prior / "neural.jsonl").open():
        row = json.loads(line)
        if row["phase"] == "baseline":
            prior_responses[("baseline", row["input"])] = row
        elif row["phase"] == "recall" and row["arm"] == "paired":
            prior_responses[(row["seed"], row["mapping"], row["input"])] = row

    def measure(indices=None, duration=500, pulse=None, learning=False, frozen=True, trace_bins=False):
        brain.weights_frozen = frozen
        before = memory_state(brain)
        stimulation = [] if indices is None else [(indices, parameters["kc_current"])]
        if pulse is not None:
            stimulation.append((c[pulse], 20))
        boundaries = list(range(0, 101, 4)) + list(range(110, 501, 10)) if trace_bins else [0, duration]
        counts = np.zeros(brain.n, dtype=np.int32)
        trace = []
        for start, end in zip(boundaries, boundaries[1:]):
            chunk, _ = brain.step(dark, end - start, stimulation=stimulation, learning=learning, lamina_bias=0)
            counts += chunk
            if trace_bins:
                trace.append({"start_ms": start, "end_ms": end, "selected_KC_counts": chunk[indices].tolist(),
                              "output_counts": {name: chunk[ix].tolist() for name, ix in outputs.items()}})
        hz = {name: float(counts[ix].mean() * 1000 / duration) for name, ix in outputs.items()}
        score = hz["MBON11"] - hz["MBON07"] - offset
        after = memory_state(brain)
        if frozen:
            assert before == after
        return {"output_hz": hz, "score_hz": score,
                "action": 1 if score >= threshold else 0 if score <= -threshold else -1,
                "spikes_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
                "memory_before": before, "memory_after": after, "trace": trace,
                "duration_ms": duration, "pulse": pulse, "learning": learning, "frozen": frozen,
                "KC_spikes": int(counts[c["kc"]].sum()),
                "DAN_spikes": {name: int(counts[c[name]].sum()) for name in ("reward", "aversive")}}

    def evaluate(context, keys=None, expected=None):
        nonlocal measured
        before = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        responses = {}
        for key in inputs if keys is None else keys:
            brain.reset(keep_memory=True)
            row = measure(inputs[key], trace_bins=True)
            if expected is not None:
                assert all(row[field] == expected[key][field] for field in ("spikes_sha256", "memory_before", "memory_after", "trace", "score_hz", "action"))
            if context["phase"] in ("baseline", "inherited") and key in prior_input_keys:
                ref_key = ("baseline", key) if context["phase"] == "baseline" else (context["seed"], context["mapping"], key)
                assert all(row[field] == prior_responses[ref_key][field] for field in ("spikes_sha256", "memory_before", "memory_after", "trace", "score_hz", "action"))
            responses[key] = row
            log.write(json.dumps({**context, "input": key, **row}) + "\n")
            measured += 1
        log.flush()
        after = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        assert before == after
        weight_checks.append({**context, "before_sha256": before, "after_sha256": after, "inputs": len(responses)})
        return responses

    brain.reset(keep_memory=False)
    baseline = evaluate({"phase": "baseline"})
    results = []
    with gzip.open(args.out / "episodes.jsonl.gz", "xt", compresslevel=6) as episodes:
        for source_run in source_summary["runs"]:
            seed, mapping = source_run["seed"], source_run["mapping"]
            path = SOURCE / f"{seed}-{mapping}-paired-memory.npz"
            with np.load(path, allow_pickle=False) as saved:
                assert np.array_equal(saved["edge_indices"], c["edges"])
                inherited_weights, inherited_u, inherited_w = (saved[k].copy() for k in ("weights", "u", "w"))
            references.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            brain.reset(keep_memory=False)
            brain.weight[c["edges"]], brain.memory_u[:], brain.memory_w[:] = inherited_weights, inherited_u, inherited_w
            inherited_state = memory_state(brain)
            assert inherited_state == source_run["arms"]["paired"]["memory"]
            inherited_full = hashlib.sha256(brain.weight.tobytes()).hexdigest()
            inherited = evaluate({"seed": seed, "mapping": mapping, "phase": "inherited"})
            arms = {}
            for arm in arm_names:
                brain.reset(keep_memory=False)
                brain.weight[c["edges"]], brain.memory_u[:], brain.memory_w[:] = inherited_weights, inherited_u, inherited_w
                assert memory_state(brain) == inherited_state
                for trial, scheduled in enumerate(schedules[str(seed)]):
                    item = undo_contexts[scheduled["context"]]
                    target = (scheduled["inconsistent_label"] if arm == "inconsistent" else item["label"]) ^ mapping
                    pulse = None if arm == "no_feedback" else "reward" if target else "aversive"
                    brain.reset(keep_memory=True)
                    decision = measure(inputs[item["input"]])
                    phases = [measure(duration=200, pulse=pulse, learning=arm != "frozen", frozen=arm == "frozen"),
                              measure(duration=250, frozen=arm == "frozen")]
                    brain.reset(keep_memory=True)
                    opposite = None if pulse is None else "aversive" if pulse == "reward" else "reward"
                    phases.extend([measure(duration=200, pulse=opposite),
                                   measure(inputs[item["input"]], learning=arm != "frozen", frozen=arm == "frozen"),
                                   measure(duration=250, frozen=arm == "frozen")])
                    training_log.write(json.dumps({"seed": seed, "mapping": mapping, "arm": arm, "trial": trial,
                                                   **scheduled, "input": item["input"], "true_label": item["label"],
                                                   "taught_raw_target": target, "decision": decision, "phases": phases}) + "\n")
                    if (trial + 1) % 30 == 0:
                        training_log.flush()
                        print(json.dumps({"seed": seed, "mapping": mapping, "arm": arm, "epoch_done": (trial + 1) // 30}), flush=True)
                state = memory_state(brain)
                saved_weights = brain.weight[c["edges"]].copy()
                delta = {"weights": int(np.count_nonzero(saved_weights != inherited_weights)),
                         "u": int(np.count_nonzero(brain.memory_u != inherited_u)),
                         "w": int(np.count_nonzero(brain.memory_w != inherited_w))}
                np.savez_compressed(args.out / f"{seed}-{mapping}-{arm}-memory.npz", edge_indices=c["edges"], weights=saved_weights, u=brain.memory_u, w=brain.memory_w)
                recall = evaluate({"seed": seed, "mapping": mapping, "arm": arm, "phase": "recall"})
                undo_actions = [recall[r["input"]]["action"] for r in undo_contexts]
                undo_semantic = np.array([a if a == -1 else a ^ mapping for a in undo_actions])
                undo_score = classification_metrics(np.array([r["label"] for r in undo_contexts]), undo_semantic)
                undo_score["minimum_target_margin_hz"] = min((1 if r["label"] ^ mapping else -1) * recall[r["input"]]["score_hz"] - threshold for r in undo_contexts)
                policy_results = {}
                for policy in POLICIES:
                    contexts = [r for r in place_contexts if r["policy"] == policy]
                    raw = [recall[r["input"]]["action"] for r in contexts]
                    semantic = [a if a == -1 else a ^ mapping for a in raw]
                    placement = probe_metrics(contexts, semantic)
                    completed = []
                    for case in cases:
                        if case["split"] != "development":
                            continue
                        result = play_with_undo(case, recall, templates, groups, undo_groups, policy, mapping)
                        episodes.write(json.dumps({"seed": seed, "mapping": mapping, "arm": arm, "policy": policy, **result}) + "\n")
                        completed.append(result)
                    sequence = {f"{blanks}-{stratum}": {"puzzles": len(subset), "solved": sum(r["solved"] for r in subset),
                                "solve_rate": float(np.mean([r["solved"] for r in subset])),
                                "timeouts": sum(r["timeouts"] for r in subset), "undo_count": sum(r["undo_count"] for r in subset)}
                                for blanks in (2, 3, 4) for stratum in ("easy", "trap")
                                for subset in [[r for r in completed if r["blanks"] == blanks and r["stratum"] == stratum]] if subset}
                    policy_results[policy] = {"placement": placement, "sequence": sequence}
                brain.weight[c["edges"]] = brain.baseline_plastic
                assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_hash
                brain.reset(keep_memory=False)
                brain.weight[c["edges"]], brain.memory_u[:], brain.memory_w[:] = inherited_weights, inherited_u, inherited_w
                assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == inherited_full
                assert memory_state(brain) == inherited_state
                evaluate({"seed": seed, "mapping": mapping, "arm": arm, "phase": "stage_erased"}, ablation_keys, inherited)
                brain.reset(keep_memory=False)
                assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_hash
                evaluate({"seed": seed, "mapping": mapping, "arm": arm, "phase": "erased"}, ablation_keys, baseline)
                if arm == "frozen":
                    assert state == inherited_state and delta == {"weights": 0, "u": 0, "w": 0}
                    assert all(recall[k]["spikes_sha256"] == inherited[k]["spikes_sha256"] for k in inputs)
                arms[arm] = {"undo": undo_score, "policies": policy_results, "memory": state,
                             "delta_from_inherited": delta, "changed_response_inputs": sum(recall[k]["spikes_sha256"] != inherited[k]["spikes_sha256"] for k in inputs),
                             "familiar_placement_retained": all(recall[k]["action"] == inherited[k]["action"] for k in familiar),
                             "familiar_placement_correct": sum(recall[k]["action"] == inherited[k]["action"] for k in familiar),
                             "stage_erasure_exact": True, "full_erasure_exact": True, "nonplastic_unchanged": True}
                print(json.dumps({"seed": seed, "mapping": mapping, "arm": arm, "undo": undo_score,
                                  "retained": arms[arm]["familiar_placement_retained"],
                                  "solves": {p: {k: v['solve_rate'] for k, v in row['sequence'].items()} for p, row in policy_results.items()}}), flush=True)
            paired = arms["paired"]
            recall_gate = paired["undo"]["balanced_accuracy"] >= .90 and min(paired["undo"]["class_recall"].values()) >= .85
            gate = None if args.paired_only else (recall_gate and
                    all(paired["undo"]["balanced_accuracy"] >= arms[a]["undo"]["balanced_accuracy"] + .25 for a in ("frozen", "no_feedback", "inconsistent")))
            prior_run = next(r for r in prior_summary["runs"] if r["seed"] == seed and r["mapping"] == mapping)
            occupancy_gates = {}
            for policy, row in paired["policies"].items():
                scored = row["placement"]
                occupancy_gates[policy] = (scored["nonempty"]["balanced_accuracy"] >= .90 and
                    all(value >= .85 for n, group in scored["by_distinct_peers"].items() if n != "0" for value in group["class_recall"].values()) and
                    all(scored["nonempty"]["balanced_accuracy"] >= prior_run["arms"][a]["policies"][policy]["probe"]["nonempty"]["balanced_accuracy"] + .25
                        for a in ("frozen", "no_feedback", "inconsistent")))
            results.append({"seed": seed, "mapping": mapping, "arms": arms, "undo_gate": gate,
                            "undo_recall_gate": recall_gate, "current_occupancy_gates": occupancy_gates,
                            "retention_gate": paired["familiar_placement_retained"],
                            "sequence_gates": {p: all(v["solve_rate"] >= .90 for v in row["sequence"].values()) for p, row in paired["policies"].items()}})
            (args.out / "partial-results.json").write_text(json.dumps(results, indent=2) + "\n")
    log.close()
    training_log.close()
    (args.out / "full-weight-checks.json").write_text(json.dumps(weight_checks, indent=2) + "\n")
    (args.out / "memory-references.json").write_text(json.dumps(references, indent=2) + "\n")
    summary = {"stage5_complete": False, "undo_gate": None if args.paired_only else all(r["undo_gate"] for r in results),
               "controls_evaluated": not args.paired_only,
               "undo_recall_gate": all(r["undo_recall_gate"] for r in results),
               "current_occupancy_gates": {p: all(r["current_occupancy_gates"][p] for r in results) for p in POLICIES},
               "retention_gate": all(r["retention_gate"] for r in results), "prior_occupancy_gates": prior_summary["policy_gates"],
               "sequence_gates": {p: all(r["sequence_gates"][p] for r in results) for p in POLICIES},
               "runs": results, "measured_neural_evaluations": measured, "elapsed_seconds": time.perf_counter() - started,
               "files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.out.iterdir()) if p.is_file()}}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("stage5_complete", "undo_gate", "retention_gate", "sequence_gates", "elapsed_seconds")}), flush=True)


if __name__ == "__main__":
    main()
