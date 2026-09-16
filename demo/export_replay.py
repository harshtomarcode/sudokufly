"""Export verified recorded decisions, spike bins, and anatomical edges.

Run from any directory with the repository's existing .venv Python. This reads
saved experiments only; it neither simulates neurons nor solves new puzzles.
"""

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.feather as feather


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/level-05/007-controlled-recovery/heldout"
SEED, MAPPING = 20260919, 0
PILOT = ROOT / "experiments/level-06/001-cautious-choice/development"
PILOT_CASE = "b4-0009393db5453f62"  # First lexicographic four-blank development trap, using the original stratum.


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def records(path):
    with gzip.open(path, "rt") as stream:
        for line in stream:
            yield json.loads(line)


def peer_cells(board, target):
    return [i for i, value in enumerate(board) if value and i != target and
            (i // 4 == target // 4 or i % 4 == target % 4 or
             (i // 8, i % 4 // 2) == (target // 8, target % 4 // 2))]


def verify_episode(episode, inputs, placement, undo):
    """Independently apply logged decisions and check the unaltered final board."""
    initial = episode["initial_board"]
    board, stack, undos = list(initial), [], 0
    exported = []
    for event in episode["events"]:
        assert board == event["board_before"] and stack == event["stack_before"]
        assert len(board) == 16 and all(0 <= value <= 4 for value in board)
        target = event["target"]
        attended = peer_cells(board, target)
        peers = tuple(sorted({board[i] for i in attended}))
        assert event["distinct_peers"] == len(peers)
        raw = inputs[event["input"]]["raw_action"]
        assert event["raw_action"] == raw
        action = raw if raw == -1 else raw ^ MAPPING
        assert event["action"] == action
        popped = None
        if event["op"] == "place":
            assert board[target] == 0 and 1 <= event["candidate"] <= 4
            assert event["input"] == placement[(peers, event["candidate"])]
            if action == 1:
                board[target] = event["candidate"]
                stack.append([target, event["candidate"]])
        else:
            assert event["op"] == "undo" and event["candidate"] is None
            assert (event["input"], event["presence_code"]) == undo[peers]
            if action == 1 and stack:
                popped = stack.pop()
                assert not initial[popped[0]] and board[popped[0]] == popped[1]
                board[popped[0]] = 0
                undos += 1
        assert event["popped"] == popped and event["undo_executed"] == (popped is not None)
        assert board == event["board_after"] and stack == event["stack_after"]
        assert undos == event["undos"]
        assert all(not value or board[i] == value for i, value in enumerate(initial))
        exported.append({**event, "peer_cells": attended, "peer_values": list(peers)})
    assert board == episode["final_board"] and stack == episode["final_stack"]
    units = ([board[i:i + 4] for i in range(0, 16, 4)] +
             [board[i::4] for i in range(4)] +
             [[board[r * 4 + c] for r in range(top, top + 2) for c in range(left, left + 2)]
              for top in (0, 2) for left in (0, 2)])
    assert episode["solved"] == all(set(unit) == {1, 2, 3, 4} for unit in units)
    assert undos == episode["undo_count"] and len(exported) == episode["decisions"]
    return exported


def anatomical_locations(ids, inputs, outputs):
    """Use source soma coordinates; absent locations remain explicitly null."""
    path = ROOT / "data/annotations.feather"
    source = read_json(ROOT / "data/source.lock.json")[path.name]
    assert sha256(path) == source["sha256"]
    annotations = feather.read_table(path, columns=["bodyId", "type", "superclass", "somaSide", "somaNeuromere", "somaLocation"])
    annotations = annotations.to_pandas().set_index("bodyId").loc[ids]
    located = annotations.somaLocation.apply(lambda xyz: isinstance(xyz, np.ndarray) and xyz.shape == (3,) and np.all(np.isfinite(xyz)))
    selected_ids = {int(neuron) for row in inputs.values() for neuron in row["kc_ids"]} | {int(row["id"]) for row in outputs}
    neurons = {}
    for neuron in sorted(selected_ids):
        row = annotations.loc[neuron]
        neurons[str(neuron)] = {"xyz": row.somaLocation.tolist() if located.loc[neuron] else None,
                               "type": row.type, "side": row.somaSide, "superclass": row.superclass}
        assert row.superclass == "cb_intrinsic"
    for output in outputs:
        assert annotations.index[output["index"]] == int(output["id"])
        assert annotations.iloc[output["index"]].type == output["type"]
        output["xyz"] = neurons[output["id"]]["xyz"]

    # Anatomical context only: uniformly sample known brain cells, never VNC
    # cells. This fixed sampling seed has no role in input or action selection.
    kc = annotations.type.fillna("").str.startswith("KC")
    background = [{"id": str(neuron), "xyz": row.somaLocation.tolist(), "group": "kenyon_cell"}
                  for neuron, row in annotations[kc & located].iterrows()]
    available = {"kenyon_cell": len(background)}
    rng = np.random.default_rng(20260914)
    for superclass, group, count in (("cb_intrinsic", "central_brain", 1000), ("ol_intrinsic", "optic_lobe", 1000)):
        pool = annotations[located & ~kc & annotations.superclass.eq(superclass)]
        available[group] = len(pool)
        for position in sorted(rng.choice(len(pool), min(count, len(pool)), replace=False).tolist()):
            row = pool.iloc[position]
            background.append({"id": str(pool.index[position]), "xyz": row.somaLocation.tolist(), "group": group})
    brain_xyz = np.stack(annotations[located & annotations.superclass.isin(["cb_intrinsic", "ol_intrinsic"])].somaLocation.values)
    kc_xyz = np.stack(annotations[kc & located].somaLocation.values)
    selected_xyz = np.array([row["xyz"] for row in neurons.values() if row["xyz"] is not None])
    return {"neurons": neurons, "background": background,
            "bounds": {"min": brain_xyz.min(axis=0).tolist(), "max": brain_xyz.max(axis=0).tolist()},
            "selected_bounds": {"min": selected_xyz.min(axis=0).tolist(), "max": selected_xyz.max(axis=0).tolist()},
            "kc_bounds": {"min": kc_xyz.min(axis=0).tolist(), "max": kc_xyz.max(axis=0).tolist()},
            "source": {"path": str(path.relative_to(ROOT)), **source, "field": "somaLocation"},
            "missing_ids": [neuron for neuron, row in neurons.items() if row["xyz"] is None],
            "counts": {"selected": len(neurons), "selected_located": len(selected_xyz), "all_kcs": int(kc.sum()),
                       "all_kcs_located": int((kc & located).sum()), "background": len(background), "available_brain_somas": available},
            "projection": {"horizontal_axis": "x", "vertical_axis": "y", "depth_axis": "z",
                           "units": "Original integer somaLocation coordinates, unchanged from the source annotation file.",
                           "coordinate_documentation": "https://male-cns.janelia.org/download/",
                           "coordinate_context": "Official MaleCNS documentation describes the raw EM volume, synapse locations and SWC skeletons in 8 nm units. The exported somaLocation integers are retained without conversion.",
                           "side": "Increasing x runs from anatomical right toward anatomical left, as checked against somaSide labels.",
                           "orientation": "Dataset-coordinate view. Local annotations alone do not establish anterior/dorsal polarity of y and z."},
            "notes": ["Each point is an actual soma annotation, not a measured activation position along a neurite.",
                      "Missing locations remain null and must not be positioned inside the anatomy.",
                      "The background contains all 4050 located Kenyon cells and a deterministic sample of 1000 other central-brain and 1000 optic-lobe intrinsic neurons from the retained graph. It is anatomical context, not recorded activity.",
                      "No VNC superclass enters this brain background. Missing somaNeuromere alone was not used to identify brain cells.",
                      "Connections join soma locations for display only; edge geometry does not reconstruct axons, dendrites, or synapse positions.",
                      "Any fly-body illustration is context, not a registration of the MaleCNS coordinates to that drawing."]}


def export_response(row, key, registry, memory, arrays, index_by_id, output_by_index, decoder):
    """Verify recorded spikes and bind displayed edges to this exact checkpoint."""
    weight_by_edge = dict(zip(memory["edge_indices"].tolist(), memory["weights"].tolist()))
    assert row["frozen"] and not row["learning"] and row["pulse"] is None
    assert row["duration_ms"] == 500 and row["memory_before"] == row["memory_after"]
    for name, field in (("weights", "sha256"), ("u", "u_sha256"), ("w", "w_sha256")):
        assert hashlib.sha256(memory[name].tobytes()).hexdigest() == row["memory_before"][field]
    kc_ids = registry[key]["KC_ids"]
    indices = np.array([index_by_id[value] for value in kc_ids], dtype=np.int32)
    assert np.all(indices[:-1] < indices[1:]) and hashlib.sha256(indices.tobytes()).hexdigest() == key
    trace, counts, previous_end = [], np.zeros(6, dtype=int), 0
    for sample in row["trace"]:
        assert sample["start_ms"] == previous_end and sample["end_ms"] > previous_end
        kc = sample["selected_KC_counts"]
        output = sample["output_counts"]["MBON07"] + sample["output_counts"]["MBON11"]
        assert len(kc) == len(kc_ids) and len(output) == 6 and min(kc + output) >= 0
        counts += output
        trace.append({"start_ms": sample["start_ms"], "end_ms": sample["end_ms"], "kc": kc, "output": output})
        previous_end = sample["end_ms"]
    assert previous_end == 500
    assert counts[:4].mean() * 2 == row["output_hz"]["MBON07"]
    assert counts[4:].mean() * 2 == row["output_hz"]["MBON11"]
    score = row["output_hz"]["MBON11"] - row["output_hz"]["MBON07"] - decoder["offset_hz"]
    threshold = decoder["threshold_hz"]
    assert score == row["score_hz"] and row["action"] == (1 if score >= threshold else 0 if score <= -threshold else -1)
    edges = []
    for kc_id, index in zip(kc_ids, indices):
        for edge in range(arrays["ptr"][index], arrays["ptr"][index + 1]):
            target = int(arrays["post"][edge])
            if target in output_by_index:
                baseline = float(arrays["weight"][edge])
                assert baseline > 0 and edge in weight_by_edge
                weight = weight_by_edge[edge]
                edges.append({"source": str(kc_id), "target": output_by_index[target]["id"],
                              "edge_index": edge, "weight": weight, "baseline_weight": baseline,
                              "efficacy": weight / baseline})
    return {"kc_ids": list(map(str, kc_ids)), "edges": edges, "trace": trace,
                   "output_hz": row["output_hz"], "score_hz": score, "raw_action": row["action"],
                   "KC_spikes": row["KC_spikes"], "DAN_spikes": row["DAN_spikes"],
                   "spikes_sha256": row["spikes_sha256"]}


def main():
    protocol, summary = read_json(SOURCE / "protocol.json"), read_json(SOURCE / "summary.json")
    assert summary["gate_passed"] and summary["no_new_learning"] and protocol["split"] == "heldout"
    for name, expected in summary["files_sha256"].items():
        assert sha256(SOURCE / name) == expected, f"Recorded artifact changed: {name}"
    for name, expected in protocol["source_sha256"].items():
        assert sha256(ROOT / name) == expected, f"Frozen source changed: {name}"

    # The old circuit report records output identities; graph indices confirm them.
    circuit_path = ROOT / "experiments/level-01/001-visual-cues/protocol.json"
    circuit = read_json(circuit_path)["circuit"]
    outputs = sorted(circuit["memory_outputs"], key=lambda row: (row["type"], row["index"]))
    assert [row["type"] for row in outputs] == ["MBON07"] * 4 + ["MBON11"] * 2
    graph = np.load(ROOT / "data/graph.npz")
    arrays = {name: graph[name] for name in ("ptr", "post", "weight", "ids")}
    graph_checks = read_json(ROOT / "data/setup-verification.json")["graph_array_hashes"]
    for name, array in arrays.items():
        assert hashlib.sha256(array.tobytes()).hexdigest() == graph_checks[name]
    assert hashlib.sha256(arrays["weight"].tobytes()).hexdigest() == protocol["initial_weights_sha256"]
    assert all(str(arrays["ids"][row["index"]]) == row["id"] for row in outputs)
    index_by_id = {int(value): i for i, value in enumerate(arrays["ids"])}
    output_by_index = {row["index"]: row for row in outputs}

    memory_path = ROOT / protocol["development"] / f"{SEED}-{MAPPING}-paired-memory.npz"
    reference = next(row for row in read_json(SOURCE / "memory-references.json")
                     if ROOT / row["path"] == memory_path)
    assert sha256(memory_path) == reference["sha256"]
    memory = np.load(memory_path)
    assert hashlib.sha256(memory["edge_indices"].tobytes()).hexdigest() == circuit["plastic_edges_sha256"]
    episodes = [row for row in records(SOURCE / "episodes.jsonl.gz")
                if (row["seed"], row["mapping"], row["arm"], row["view"]) == (SEED, MAPPING, "paired", "base")]
    pools = [
        ("Learned recovery", "An initially legal guess leads to a dead end. The recorded fly policy uses Undo and finishes.",
         [row for row in episodes if row["blanks"] == 4 and row["stratum"] == "trap" and row["solved"] and row["undo_count"]]),
        ("Straightforward solve", "Four missing digits filled by the same learned policy, without executing Undo.",
         [row for row in episodes if row["blanks"] == 4 and row["stratum"] == "easy" and row["solved"]]),
        ("A remaining loop", "A recorded failure: the board and placement stack repeat, so the run stops unfinished.",
         [row for row in episodes if row["end"] == "repeated_state"]),
    ]
    selected = [(title, description, min(pool, key=lambda row: (len(row["events"]), row["case_id"])))
                for title, description, pool in pools]
    needed = {event["input"] for _, _, episode in selected for event in episode["events"]}
    registry = read_json(SOURCE / "inputs.json")
    inputs = {}
    for row in records(SOURCE / "neural.jsonl.gz"):
        if (row.get("seed"), row.get("mapping"), row.get("arm"), row["phase"]) != (SEED, MAPPING, "paired", "recall"):
            continue
        key = row["input"]
        if key not in needed:
            continue
        assert key not in inputs
        inputs[key] = export_response(row, key, registry, memory, arrays, index_by_id, output_by_index, protocol["decoder"])
    assert set(inputs) == needed
    placement = {(tuple(row["peers"]), row["candidate"]): row["input"]
                 for row in read_json(SOURCE / "contexts.json") if row["policy"] == "separate-occupancy"}
    undo = {tuple(row["peers"]): (row["input"], row["pattern"]) for row in read_json(SOURCE / "undo-contexts.json")}
    cases = [{"id": episode["case_id"], "title": title, "description": description,
              **{key: episode[key] for key in ("stratum", "blanks", "initial_board", "final_board", "solved", "end", "undo_count", "sweeps", "first_loop")},
              "events": verify_episode(episode, inputs, placement, undo)} for title, description, episode in selected]
    pilot_meta = None
    if (PILOT / "summary.json").exists() and read_json(PILOT / "summary.json")["pilot_gate"]:
        pilot_summary, pilot_protocol = read_json(PILOT / "summary.json"), read_json(PILOT / "protocol.json")
        assert not pilot_summary["heldout_evaluated"] and not pilot_summary["stage6_complete"]
        assert pilot_protocol["seed"] == SEED and pilot_protocol["decoder"] == protocol["decoder"]
        for name, expected in pilot_summary["files_sha256"].items():
            assert sha256(PILOT / name) == expected, f"Pilot artifact changed: {name}"
        for name, expected in pilot_protocol["source_sha256"].items():
            assert sha256(ROOT / name) == expected, f"Pilot source changed: {name}"
        pilot_run = next(row for row in pilot_summary["runs"] if row["mapping"] == MAPPING)
        assert pilot_run["pilot_gate"] and pilot_run["selected_epoch"] is not None
        epoch = pilot_run["selected_epoch"]
        pilot_cases = read_json(PILOT / "cases.json")
        assert min(row["id"] for row in pilot_cases if row["blank_count"] == 4 and row["stratum"] == "trap") == PILOT_CASE
        case = next(row for row in pilot_cases if row["id"] == PILOT_CASE)
        assert case["split"] == "development"
        episode = next(row for row in records(PILOT / "episodes.jsonl.gz")
                       if (row["mapping"], row["arm"], row["epoch"], row["case_id"]) == (MAPPING, "paired", epoch, PILOT_CASE))
        assert episode["solved"] and episode["wrong_placements"] == 0 and episode["end"] == "filled"
        pilot_memory_path = PILOT / f"{MAPPING}-paired-epoch-{epoch:02d}-memory.npz"
        pilot_memory = np.load(pilot_memory_path)
        assert np.array_equal(pilot_memory["edge_indices"], memory["edge_indices"])
        pilot_needed = {offer["input"] for assessment in episode["assessments"] for offer in assessment["offers"]}
        for row in records(PILOT / "neural.jsonl.gz"):
            if (row["mapping"], row["arm"], row["epoch"]) != (MAPPING, "paired", epoch) or row["input"] not in pilot_needed:
                continue
            key = row["input"]
            assert "pilot:" + key not in inputs
            inputs["pilot:" + key] = export_response(row, key, registry, pilot_memory, arrays, index_by_id, output_by_index, pilot_protocol["decoder"])
        assert all("pilot:" + key in inputs for key in pilot_needed)
        board, events, assessments, offers_seen = list(case["board"]), [], [], 0
        assert board == episode["initial_board"]
        for round_index, assessment in enumerate(episode["assessments"]):
            assert board == assessment["board"]
            offers = assessment["offers"]
            assert [(offer["target"], offer["candidate"]) for offer in offers] == [
                (target, digit) for target in range(16) if not board[target] for digit in range(1, 5)]
            for offer in offers:
                target, candidate, key = offer["target"], offer["candidate"], offer["input"]
                peers = tuple(sorted({board[i] for i in peer_cells(board, target)}))
                assert key == placement[peers, candidate]
                response = inputs["pilot:" + key]
                assert offer["raw_action"] == response["raw_action"]
                assert offer["action"] == (offer["raw_action"] if offer["raw_action"] == -1 else offer["raw_action"] ^ MAPPING)
                assert offer["score_hz"] == (1 - 2 * MAPPING) * response["score_hz"]
            accepted = [offer for offer in offers if offer["action"] == 1]
            chosen = max(accepted, key=lambda offer: offer["score_hz"]) if accepted else None
            assert chosen is not None and chosen == assessment["chosen"]
            event = episode["events"][round_index]
            assert all(event[key] == value for key, value in chosen.items())
            assert event["board_before"] == board and event["assessment"] == round_index
            attended = peer_cells(board, chosen["target"])
            peers = sorted({board[i] for i in attended})
            board[chosen["target"]] = chosen["candidate"]
            assert board == event["board_after"]
            offers_seen += len(offers)
            assessments.append({"board": assessment["board"], "offers": [
                {**offer, "input": "pilot:" + offer["input"], "selected": offer == chosen} for offer in offers]})
            events.append({**event, "input": "pilot:" + event["input"], "distinct_peers": len(peers),
                           "peer_cells": attended, "peer_values": peers, "undo_executed": False, "popped": None,
                           "assessment_count": len(offers), "assessments_so_far": offers_seen})
        assert board == episode["final_board"] == case["solution"]
        assert len(events) == len(episode["events"]) == case["blank_count"] and offers_seen == episode["neural_offers"]
        pilot_meta = {"source": str(PILOT.relative_to(ROOT)), "summary_sha256": sha256(PILOT / "summary.json"),
                      "memory": {"path": str(pilot_memory_path.relative_to(ROOT)), "sha256": sha256(pilot_memory_path)},
                      "seed": SEED, "mapping": MAPPING, "epoch": epoch, "split": "development",
                      "selection": "First lexicographic four-blank development trap in the original stratum; chosen after training to illustrate ambiguity, without filtering on new policy outcomes.",
                      "selector": pilot_protocol["selector"]}
        cases.insert(0, {"id": PILOT_CASE, "title": "Careful choices", "mode": "cautious", "source": pilot_meta,
                         "description": "A development pilot learns to defer ambiguous offers. Every empty cell and digit is assessed; the fixed selector chooses the highest accepted neural score.",
                         "stratum": episode["stratum"], "blanks": episode["blanks"], "initial_board": episode["initial_board"],
                         "final_board": board, "solved": True, "end": "filled", "undo_count": 0,
                         "events": events, "assessments": assessments, "neural_offers": offers_seen})
    anatomy = anatomical_locations(arrays["ids"], inputs, outputs)
    data = {"meta": {"source": str(SOURCE.relative_to(ROOT)), "seed": SEED, "mapping": MAPPING,
                     "view": "base", "recorded": True, "graph": protocol["graph"], "decoder": protocol["decoder"],
                     "summary_sha256": sha256(SOURCE / "summary.json"), "source_files_sha256": summary["files_sha256"],
                     "memory": reference, "pilot": pilot_meta, "circuit_protocol_sha256": sha256(circuit_path),
                     "notes": ["Recorded, frozen 500 ms input-response trials are reused by the recorded board driver; this is not a live simulation.",
                               "Highlighted cells receive engineered sensory input. Node flashes show their measured spike counts in recorded time bins.",
                               "Lines are actual KC-to-MBON anatomical edges, with trained weights. Lighting a line indicates its source cell spiked, not measured causal flow through that synapse.",
                               "Soma positions come from MaleCNS annotations; any connecting lines are schematic, not traced neurites. The full retained graph contains 166700 neurons and 25582938 directed edges.",
                               "DAN totals are observed spikes, not external reward. Learning and external dopamine teaching were disabled during replay.",
                               "Trap denotes failure of a first-legal greedy scan. Favorable conservative controls solved all 160 reserved boards without new Step 5 learning."]},
            "outputs": outputs, "cases": cases, "inputs": inputs, "anatomy": anatomy}
    target = Path(__file__).with_name("data.js")
    target.write_text("// Generated by demo/export_replay.py from hash-verified recorded experiments.\nwindow.FLY_DEMO_DATA=" +
                      json.dumps(data, separators=(",", ":"), allow_nan=False) + ";\n")
    print(json.dumps({"output": str(target), "bytes": target.stat().st_size, "cases": [
        {"id": row["id"], "events": len(row["events"]), "solved": row["solved"], "undos": row["undo_count"]} for row in cases],
        "inputs": len(inputs), "events_verified": sum(len(row["events"]) for row in cases),
        "traces_verified": len(inputs), "anatomical_edges": len({edge["edge_index"] for row in inputs.values() for edge in row["edges"]}),
        "anatomical_locations": anatomy["counts"], "missing_location_ids": anatomy["missing_ids"]}, indent=2))


if __name__ == "__main__":
    main()
