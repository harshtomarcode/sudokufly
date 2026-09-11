"""Image-derived cue learning and four-symbol comparison with local fly plasticity.

One fixed random sensory adapter; no equality operation or labels in encoding.
See each recorded protocol for the changed sensory/readout assumptions.
"""

import argparse
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

from sudokufly import ROOT, UPSTREAM, UPSTREAM_COMMIT, cue_frame, memory_state


def render(case, view):
    """Environment renderer only: target labels are not arguments."""
    if case["task"] == "cues":
        frame = cue_frame(case["cue"])
        if view in ("thin", "thick"):
            width = 10 if view == "thin" else 14
            frame.fill(235)
            if case["cue"] == "vertical":
                for x in (116, 154, 192):
                    frame[42:138, x:x + width] = 24
            else:
                for y in (46, 84, 122):
                    frame[y:y + width, 112:208] = 24
        if view == "shift":
            frame = np.roll(np.roll(frame, 3, axis=1), -2, axis=0)
        return frame
    frame = Image.new("RGB", (192, 64), "white")
    draw = ImageDraw.Draw(frame)
    font = ImageFont.load_default(size=32 if view != "small" else 28)
    glyphs = [*case["row"], *([None] * (2 - len(case["row"]))), case["candidate"]]
    for slot, glyph in enumerate(glyphs):
        if glyph is None:
            continue
        text = str(glyph + 1)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=0)
        x = slot * 64 + (64 - (box[2] - box[0])) // 2 - box[0]
        y = (64 - (box[3] - box[1])) // 2 - box[1]
        if view == "shift":
            x += 3
            y -= 2
        draw.text((x, y), text, fill="black", font=font, stroke_width=1 if view == "bold" else 0)
    return np.asarray(frame)


def patch_pixels(frame):
    """Fixed geometric normalization; neither glyph identity nor comparison."""
    gray = np.asarray(Image.fromarray(frame).convert("L"))
    yy, xx = np.nonzero(gray < 128)
    if not len(xx):
        return np.zeros(64, dtype=np.float64)
    crop = gray[yy.min():yy.max() + 1, xx.min():xx.max() + 1]
    resized = np.asarray(Image.fromarray(crop).resize((8, 8), Image.Resampling.BOX), dtype=np.float64)
    pixels = 1 - resized.ravel() / 255
    pixels -= pixels.mean()
    return pixels / max(np.linalg.norm(pixels), 1e-12)


def encode(frame, task, pool, filters, active, pixel_mean=None, templates=None, groups=None):
    """Label-blind random pixel features; all cross-role products treated alike."""
    if task == "cues":
        score = filters[0] @ patch_pixels(frame)
    elif templates is not None:
        # Each role has an independently permuted template bank. All Cartesian
        # pairs receive identical routing; neither identity equality nor labels
        # are computed here. Symbol recognition is explicitly template-based.
        candidate = np.argmin(np.linalg.norm(templates[0] - patch_pixels(frame[:, 128:192]), axis=1))
        codes = []
        for i in (0, 64):
            pixels = patch_pixels(frame[:, i:i + 64])
            if np.any(pixels):
                row = np.argmin(np.linalg.norm(templates[1] - pixels, axis=1))
                codes.append(int(candidate * len(templates[1]) + row))
        # Constant total input: 16 KCs for one pair, 8 from each of two pairs.
        count = active // (2 * len(codes))
        return np.sort(np.concatenate([groups[code, :, :count].ravel() for code in codes]))
    else:
        candidate = np.maximum(filters[0] @ (patch_pixels(frame[:, 128:192]) - pixel_mean), 0)
        row = []
        for i in (0, 64):
            pixels = patch_pixels(frame[:, i:i + 64])
            row.append(np.maximum(filters[1] @ (pixels - pixel_mean), 0) if np.any(pixels) else np.zeros(len(pool)))
        score = np.maximum(candidate * row[0], candidate * row[1])
    # Fixed tie-breaking and cardinality; no outcome enters current or selection.
    if task == "symbols":
        half = len(pool) // 2
        selected = np.concatenate([start + np.lexsort((np.arange(half), -score[start:start + half]))[:active // 2]
                                   for start in (0, half)])
    else:
        selected = np.lexsort((np.arange(len(pool)), -score))[:active]
    return np.sort(pool[selected])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("probe", "pilot", "train"))
    parser.add_argument("--task", choices=("cues", "symbols"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--pool", type=int, default=256)
    parser.add_argument("--active", type=int, default=16)
    parser.add_argument("--encoder-seed", type=int, default=20260911)
    parser.add_argument("--encoder", choices=("random", "templates"), default="random")
    parser.add_argument("--training-seed", type=int, default=20260911)
    parser.add_argument("--threshold-hz", type=float)
    parser.add_argument("--kc-current", type=float, default=30)
    parser.add_argument("--mbon-current", type=float, default=5.5)
    parser.add_argument("--eta", type=float, default=0.001)
    parser.add_argument("--epochs", type=int, default=8)
    args = parser.parse_args()
    if args.mode != "probe" and args.reference is None:
        parser.error("Training needs a completed untrained reference")
    if args.pool < args.active or args.pool % 2 or args.active < 1 or args.epochs < 2 or args.epochs % 2 or (args.task == "symbols" and args.active % 2):
        parser.error("Invalid pool, active count, or epochs")
    if any(not np.isfinite(v) or v <= 0 for v in (args.kc_current, args.mbon_current, args.eta)):
        parser.error("Positive finite current and eta required")
    if args.threshold_hz is not None and (not np.isfinite(args.threshold_hz) or args.threshold_hz <= 0):
        parser.error("Positive finite threshold required")
    if args.encoder == "templates" and (args.task != "symbols" or args.active % 4):
        parser.error("Template encoder requires symbols and active divisible by four")
    upstream = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    if upstream != UPSTREAM_COMMIT or dirty:
        parser.error("Upstream must be clean and pinned")
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    os.environ["STONKFLY_DATA"] = str(ROOT / "data")
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.brain import MemoryBrain
    from stonkfly.neural.common import annotations

    graph = verify()
    started = time.perf_counter()
    brain = MemoryBrain(eta=args.eta)
    annotation = annotations(brain.ids)
    c = brain.circuit
    outputs = {t: np.flatnonzero(annotation.type.eq(t)) for t in ("MBON07", "MBON11")}
    for indices in outputs.values():
        brain.tonic[indices] = args.mbon_current
    contacts = np.rint(brain.baseline_plastic / 0.275).astype(np.int64)
    mass = {}
    for name, indices in outputs.items():
        keep = np.isin(brain.post[c["edges"]], indices)
        mass[name] = np.bincount(c["pre"][keep], weights=contacts[keep], minlength=brain.n)
    both = np.flatnonzero((mass["MBON07"] > 0) & (mass["MBON11"] > 0))
    pool = []
    for side in ("L", "R"):
        choices = [int(i) for i in both if str(annotation.instance.iloc[i]).endswith("_" + side)]
        choices.sort(key=lambda i: (-min(mass["MBON07"][i], mass["MBON11"][i]),
                                    -(mass["MBON07"][i] + mass["MBON11"][i]), int(brain.ids[i])))
        pool.extend(choices[:args.pool // 2])
    pool = np.asarray(pool, dtype=np.int32)
    if len(pool) != args.pool:
        raise RuntimeError("Insufficient anatomically supported KCs")
    rng = np.random.default_rng(args.encoder_seed)
    filters = rng.normal(size=(2, len(pool), 64))
    filters /= np.linalg.norm(filters, axis=2, keepdims=True)
    initial_hash = hashlib.sha256(brain.weight.tobytes()).hexdigest()
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    offset, threshold = 0.0, 2.0
    if args.task == "cues":
        training = [{"task": "cues", "cue": x, "label": int(i == 0)} for i, x in enumerate(("vertical", "horizontal"))]
        testing = training
        views = ("base", "shift", "thin", "thick")
    else:
        training = [{"task": "symbols", "row": [r], "candidate": q, "label": int(q != r)}
                    for r in range(4) for q in range(4)]
        testing = [{"task": "symbols", "row": list(row), "candidate": q, "label": int(q not in row)}
                   for row in itertools.permutations(range(4), 2) for q in range(4)]
        views = ("base", "shift", "small", "bold")
    training_views = ("base",) if args.task == "cues" or args.encoder == "templates" else ("base", "bold")
    pixel_mean = None if args.task == "cues" else np.mean([
        patch_pixels(render(case, view)[:, 128:192]) for case in training for view in training_views], axis=0)
    templates, groups = None, None
    if args.encoder == "templates":
        unique = {hashlib.sha256(p.tobytes()).hexdigest(): p for p in
                  [patch_pixels(render(case, "base")[:, 128:192]) for case in training]}
        bank = np.array([unique[key] for key in sorted(unique)])
        templates = np.array([bank[rng.permutation(len(bank))] for _ in range(2)])
        n_codes = len(bank) ** 2
        if args.pool != n_codes * args.active:
            raise RuntimeError("Template groups require pool == prototypes^2 * active")
        groups = np.empty((n_codes, 2, args.active // 2), dtype=np.int32)
        for side in range(2):
            for rank in range(args.active // 2):
                block = pool[side * (args.pool // 2) + rank * n_codes:side * (args.pool // 2) + (rank + 1) * n_codes]
                groups[:, side, rank] = block if rank % 2 == 0 else block[::-1]
        groups = groups[rng.permutation(n_codes)]
    encoded = {}
    manifest = []
    for split, cases, variants in (("train", training, training_views), ("test", testing, views)):
        for index, case in enumerate(cases):
            for view in variants:
                key = f"{split}-{index}-{view}"
                frame = render(case, view)
                indices = encode(frame, args.task, pool, filters, args.active, pixel_mean, templates, groups)
                encoded[key] = indices
                manifest.append({"key": key, "case": case, "view": view,
                                 "image_sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
                                 "KC_ids": brain.ids[indices].tolist()})
                if split == "train" or index < 2:
                    Image.fromarray(frame).save(args.out / f"{key}.png")
    protocol = {
        "task": args.task, "mode": args.mode, "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "imported_source_sha256": hashlib.sha256((ROOT / "sudokufly.py").read_bytes()).hexdigest(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "upstream": upstream, "graph": graph, "initial_weights_sha256": initial_hash,
        "parameters": {k: v for k, v in vars(args).items() if k not in ("mode", "out", "reference")},
        "pool_ids": brain.ids[pool].tolist(), "filter_sha256": hashlib.sha256(filters.tobytes()).hexdigest(),
        "pixel_mean": None if pixel_mean is None else pixel_mean.tolist(),
        "templates": None if templates is None else templates.tolist(),
        "group_KC_ids": None if groups is None else brain.ids[groups].tolist(),
        "sensory_adapter": "Fixed 8x8 normalized ink pixels, seeded random filters. Symbols subtract the uniform unlabeled training-patch mean, use independent candidate/cell filter products, shared max-pooling over row slots, top-k/2 KCs per hemisphere. No glyph IDs, equality or target labels enter encoding. Layout, translation normalization and row-order invariance are engineered.",
        "teaching": "Supervised valence via DAN pulses, not chosen-action correctness. Cue500ms freezes weights but accumulates traces; cue-offDAN200ms learns;250ms passive consolidation.",
        "decoder": {"score": "meanMBON11Hz-meanMBON07Hz-offset", "offset_hz": offset, "threshold_hz": threshold,
                    "calibration": "Global unlabeled training-image offset and deadband. No per-image output correction."},
        "training_cases": training, "training_views": training_views, "test_cases": testing, "views": views,
        "gates": {"cues": "Every mapping/order: >=0.90 test accuracy, >=0.25 above frozen/no-feedback/inconsistent controls; exact memory erasure and nonplastic preservation.",
                  "symbols": "Every mapping/order: >=0.90 balanced accuracy on unseen two-cell compositions, >=0.85 each class, candidate and view; >=0.25 above controls; exact erasure/nonplastic checks. Rows contain two distinct symbols from fixed alphabet1..4."},
        "limits": "Engineered visual representation and MBON readout; no claim of native fly vision, novel-symbol transfer, or Sudoku solving.",
    }
    if templates is not None:
        protocol["sensory_adapter"] = "Fixed nearest-template parsing of normalized 8x8 pixels. Templates are deduplicated unlabeled base training patches ordered by pixel hash and independently permuted by role. Every Cartesian template pair gets an identically sized disjoint KC group, stratified by anatomical strength without labels. A single pair drives16 KCs; each of two pairs drives8 (4/hemisphere). Recognition and equal row pooling are engineered; pair valence is learned only in KC-to-MBON synapses. No equality branch, membership flag, labels or trained decision head in encoding."
    if args.mode != "probe":
        reference = json.loads((args.reference / "summary.json").read_text())
        rp = json.loads((args.reference / "protocol.json").read_text())
        for key in ("source_sha256", "imported_source_sha256", "parameters", "pool_ids", "filter_sha256", "pixel_mean", "templates", "group_KC_ids", "initial_weights_sha256"):
            if rp[key] != protocol[key]:
                raise RuntimeError(f"Reference differs: {key}")
        for name, sha in reference["files_sha256"].items():
            if hashlib.sha256((args.reference / name).read_bytes()).hexdigest() != sha:
                raise RuntimeError(f"Reference artifact changed: {name}")
        if rp["mode"] != "probe":
            raise RuntimeError("Reference must be an untrained probe")
        offset, threshold = reference["decoder_offset_hz"], reference["decoder_threshold_hz"]
        protocol["decoder"].update(offset_hz=offset, threshold_hz=threshold)
        protocol["reference_sha256"] = hashlib.sha256((args.reference / "summary.json").read_bytes()).hexdigest()
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    (args.out / "inputs.json").write_text(json.dumps(manifest, indent=2) + "\n")
    log = (args.out / "trials.jsonl").open("x")
    records = []

    def measure(indices=None, duration=500, pulse=None, learn=False, frozen=True):
        brain.weights_frozen = frozen
        before = memory_state(brain)
        stimulation = []
        if indices is not None:
            stimulation.append((indices, args.kc_current))
        if pulse is not None:
            stimulation.append((c[pulse], 20))
        counts, _ = brain.step(dark, duration, stimulation=stimulation, learning=learn, lamina_bias=0)
        hz = {name: float(counts[ix].mean() * 1000 / duration) for name, ix in outputs.items()}
        raw = hz["MBON11"] - hz["MBON07"]
        score = raw - offset
        after = memory_state(brain)
        if frozen and before != after:
            raise RuntimeError("Frozen phase changed memory")
        return {"output_hz": hz, "raw_score_hz": raw, "score_hz": score,
                "action": 1 if score >= threshold else 0 if score <= -threshold else -1,
                "KC_spikes": int(counts[c["kc"]].sum()), "active_KCs": int(np.count_nonzero(counts[c["kc"]])),
                "selected_KC_spikes": int(counts[indices].sum()) if indices is not None else 0,
                "DAN_spikes": {p: int(counts[c[p]].sum()) for p in ("reward", "aversive")},
                "spikes_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
                "frozen": frozen, "learning": learn, "memory_before": before, "memory_after": after}

    def record(context, row):
        row = {**context, **row}
        log.write(json.dumps(row, allow_nan=False) + "\n")
        log.flush()
        records.append(row)
        return row

    def evaluate(context, mapping):
        rows = []
        for index, case in enumerate(testing):
            for view in views:
                brain.reset(keep_memory=True)
                row = measure(encoded[f"test-{index}-{view}"])
                target = case["label"] if mapping == 0 else 1 - case["label"]
                rows.append(record({**context, "phase": "eval", "case": index, "view": view,
                                    "target": target, "correct": row["action"] == target}, row))
        by_class = {str(t): float(np.mean([r["correct"] for r in rows if r["target"] == t])) for t in (0, 1)}
        by_candidate = {} if args.task == "cues" else {str(q): float(np.mean([r["correct"] for r in rows if testing[r["case"]]["candidate"] == q])) for q in range(4)}
        return {"accuracy": float(np.mean([r["correct"] for r in rows])), "balanced_accuracy": float(np.mean(list(by_class.values()))),
                "by_class": by_class, "by_candidate": by_candidate,
                "by_view": {v: float(np.mean([r["correct"] for r in rows if r["view"] == v])) for v in views},
                "timeouts": sum(r["action"] == -1 for r in rows), "spike_hashes": [r["spikes_sha256"] for r in rows]}

    if args.mode == "probe":
        baseline = []
        for index in range(len(training)):
            for view in training_views:
                brain.reset(keep_memory=False)
                row = record({"phase": "probe", "case": index, "view": view}, measure(encoded[f"train-{index}-{view}"]))
                baseline.append(row["raw_score_hz"])
                print(json.dumps({"case": index, "view": view, "raw_score": row["raw_score_hz"], "output": row["output_hz"], "KCs": row["active_KCs"]}), flush=True)
        result = {"decoder_offset_hz": float(np.mean(baseline)),
                  "decoder_threshold_hz": float(args.threshold_hz if args.threshold_hz is not None else max(2, max(abs(x - np.mean(baseline)) for x in baseline) + 1)),
                  "untrained_scores_hz": baseline, "no_learning_performed": True}
    else:
        results = []
        for seed in range(args.training_seed, args.training_seed + (1 if args.mode == "pilot" else 2)):
            schedule = []
            for epoch in range(args.epochs):
                chunk = [(i, view) for i, case in enumerate(training) for view in training_views
                         for _ in range(3 if args.task == "symbols" and case["label"] == 0 else 1)]
                random.Random(seed + epoch * 100).shuffle(chunk)
                schedule.extend(chunk)
            inconsistent = {}
            for i, key in enumerate(itertools.product(range(len(training)), training_views)):
                positions = [j for j, case_view in enumerate(schedule) if case_view == key]
                pulses = ["reward" if j % 2 else "aversive" for j in range(len(positions))]
                random.Random(seed + i).shuffle(pulses)
                inconsistent.update(zip(positions, pulses))
            for mapping in (0, 1):
                brain.reset(keep_memory=False)
                baseline = evaluate({"seed": seed, "mapping": mapping, "arm": "baseline"}, mapping)
                arms = {}
                for arm in (("paired",) if args.mode == "pilot" else ("paired", "frozen", "no_feedback", "inconsistent")):
                    brain.reset(keep_memory=False)
                    for trial, (index, view) in enumerate(schedule):
                        brain.reset(keep_memory=True)
                        row = measure(encoded[f"train-{index}-{view}"])
                        label = training[index]["label"] if mapping == 0 else 1 - training[index]["label"]
                        pulse = None if arm == "no_feedback" else inconsistent[trial] if arm == "inconsistent" else "reward" if label else "aversive"
                        feedback = measure(duration=200, pulse=pulse, learn=arm != "frozen", frozen=arm == "frozen")
                        consolidation = measure(duration=250, frozen=arm == "frozen")
                        record({"seed": seed, "mapping": mapping, "arm": arm, "phase": "train", "trial": trial,
                                "case": index, "view": view, "pulse": pulse, "feedback": feedback, "consolidation": consolidation}, row)
                    saved = brain.weight[c["edges"]].copy()
                    state = memory_state(brain)
                    np.savez_compressed(args.out / f"{seed}-{mapping}-{arm}-memory.npz", edge_indices=c["edges"], weights=saved, u=brain.memory_u, w=brain.memory_w)
                    evaluation = evaluate({"seed": seed, "mapping": mapping, "arm": arm}, mapping)
                    brain.weight[c["edges"]] = brain.baseline_plastic
                    if hashlib.sha256(brain.weight.tobytes()).hexdigest() != initial_hash:
                        raise RuntimeError("Nonplastic weights changed")
                    brain.weight[c["edges"]] = saved
                    brain.reset(keep_memory=False)
                    erased = evaluate({"seed": seed, "mapping": mapping, "arm": arm + "_erased"}, mapping)
                    if erased["spike_hashes"] != baseline["spike_hashes"]:
                        raise RuntimeError("Erasure failed")
                    if arm == "frozen" and evaluation["spike_hashes"] != baseline["spike_hashes"]:
                        raise RuntimeError("Frozen control failed")
                    arms[arm] = {"evaluation": evaluation, "memory": state, "erasure_exact": True, "nonplastic_unchanged": True}
                    print(json.dumps({"seed": seed, "mapping": mapping, "arm": arm,
                                      "accuracy": evaluation["accuracy"], "by_view": evaluation["by_view"],
                                      "changed_edges": state["changed_edges"]}), flush=True)
                paired = arms["paired"]["evaluation"]
                passed = args.mode == "train" and paired["balanced_accuracy"] >= .90 and min(paired["by_class"].values()) >= .85 and all(x >= .85 for x in paired["by_candidate"].values()) and min(paired["by_view"].values()) >= .85 and all(paired["balanced_accuracy"] >= arms[a]["evaluation"]["balanced_accuracy"] + .25 for a in ("frozen", "no_feedback", "inconsistent"))
                results.append({"seed": seed, "mapping": mapping, "schedule": schedule, "arms": arms, "gate_passed": passed})
                (args.out / "partial-results.json").write_text(json.dumps(results, indent=2) + "\n")
        result = {"runs": results, "gate_passed": all(r["gate_passed"] for r in results)}
    log.close()
    result.update(elapsed_seconds=time.perf_counter() - started, recorded_trials=len(records),
                  files_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.out.iterdir()) if p.is_file()})
    (args.out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"complete": str(args.out), "gate_passed": result.get("gate_passed"), "seconds": result["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
