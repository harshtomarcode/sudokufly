# Independent artifact and mechanism audit

Audited `probe`, `probe-tonic5`, and `train8` on 2026-09-10. All checks passed. This audit independently reconstructed quantities from the retained graph, protocols, phase bins, and 16 memory snapshots; it did not rerun neural simulations or modify experiment results.

## Provenance and input selection

- All **23 manifest-bound files** match their recorded SHA-256: two files per probe and 19 for training. Summary files do not hash themselves. Training additionally binds the exact tonic-probe summary by SHA-256.
- The original probe's runner hash resolves to `git show 0bb4f51:calibrate_step1.py`: `7e289d17488adcd81e57ed4981e00787f2cd85d28bc31268b789055ba6d02c82`.
- The tonic probe and training bind the audited current runner: `e3fe5296cf653e01a45053118bc58912f51c4c5c16e0552fabdb80c5eb8c8962`. All three imported `sudokufly.py` hashes match; all name pinned upstream `78ef3e05ab0fa086032098558d893667068944a0`.
- The initial whole-graph weight hash matches the retained graph; the original circuit contains 7,835 plastic edges.
- Independently reranking integer contact counts reproduces every selected neuron index, body ID, type, and contact total in all three protocols. Each cue has 16 KCs, eight per hemisphere, and the ensembles are disjoint. Each has 58 plastic edges and covers all six output neurons. Cue A has 287 MBON07 / 252 MBON11 contacts; B has 277 / 253.
- Both untrained probes have nine records, no plastic weight changes, and 112 KC spikes per cue presentation. The initial zero-background probe has raw output scores 0/0 Hz; the constant-current probe has 8.5/8.5 Hz. Its pooled **8.5 Hz offset** is exactly the offset used in training.

## Memory specificity

All 16 NPZ files have the correct edge-index arrays, finite arrays, matching reported weight/u/w hashes, and exact float32 consistency with `weight = baseline * (1 + w)`. Changed weight, u, and w masks all match the expected compartment masks.

| Arm | Snapshots | Changed edges per snapshot | Independently verified location |
|---|---:|---:|---|
| Paired | 4 | 58 | Reward cue's 32 KC→MBON07 edges and aversive cue's 26 KC→MBON11 edges |
| Frozen | 4 | 0 | All plastic weights equal baseline; u/w zero |
| No feedback | 4 | 0 | All plastic weights equal baseline; u/w zero |
| Inconsistent | 4 | 116 | Both cues' connections to both compartments |

In each paired run the other 58 stimulated-cue edges remain exactly unchanged. All **7,719 plastic edges from unstimulated KCs** remain exactly unchanged in every snapshot. Reversing the cue assignments reverses which compartment changes for each cue.

All 96 cue/target weighted means, their edge counts, and the 32 reported paired-depression margins were independently recomputed from the snapshots. For paired training, assigned-compartment weighted efficacy is **0.659785–0.660275**, while the opposite compartment remains exactly 1. The corresponding separation is **0.339725–0.340215**. Inconsistent training depresses both compartments to **0.829893–0.830195**, producing little separation. Individual saved-edge efficacy across all arms ranges from **0.659333 to 1.0**; no edges reach either clipping bound.

## Recorded activity and decisions

All **546 recorded phases** (9 + 9 + 528) have the expected number of 10 ms bins. Summing those bins independently reproduces KC and DAN counts, all output-cell firing rates, raw/centered scores, and thresholded actions. All 354 frozen phase records preserve their reported memory state exactly.

Every training cue phase records 112 KC spikes and no DAN spikes. Every feedback phase records zero KC spikes; imposed reward feedback produces 270 reward-DAN spikes, and aversive feedback produces 36 aversive-DAN spikes. Consolidation records no KC or DAN spikes. This supports the intended delayed association mechanism: cue activity leaves a trace, and the later DAN pulse changes the corresponding eligible connections. Reward and aversive populations differ in size (15 and 2); the totals correspond to an average of 18 spikes per stimulated cell.

The 16 schedules reproduce the declared cue orders, four presentations per cue, and assigned pulse sequences. Inconsistent feedback supplies each cue exactly two reward and two aversive pulses. The no-feedback arm supplies none.

| Mapping | Paired score A | Paired score B | Frozen / no-feedback A,B | Inconsistent A,B |
|---|---:|---:|---|---|
| A reward, B aversive | +5.5 Hz | −8.0 Hz | 0, 0 Hz | −2.5, −1.0 Hz |
| A aversive, B reward | −10.0 Hz | +5.5 Hz | 0, 0 Hz | −2.5, −1.0 Hz |

Both training orders produce these same scores. The frozen decoder uses ±5 Hz thresholds. Paired evaluation therefore scores 100% in all four mapping/order runs; every control response is a timeout and scores 0%. These control scores describe abstentions, not systematic wrong choices. The weakest learned acceptance score exceeds the threshold by only **0.5 Hz**.

Repeated frozen evaluations have identical recorded full-spike hashes. Erasure recovers the baseline hashes in all 16 arms; frozen and no-feedback evaluations also match baseline exactly. Recomputed accuracies, reported scores, partial results, and all four declared calibration gates agree with the final summary.

## Limits of this audit

The retained NPZ files store plastic memory only. Thus this audit directly verifies those arrays and the initial whole-graph hash; unchanged *nonplastic* weights after training rely on the runner's recorded whole-graph comparison and its inspected implementation. Likewise, full spike vectors are retained as hashes, so identical hashes establish recorded repeatability, while bin reconstruction independently checks the stored subgroup counts and decoder. This is an artifact audit, not an independent simulation replication.

The result supports controlled synthetic cue-to-valence conditioning under the declared timing, imposed input currents, constant output-cell background current, and fixed calibrated decoder. It does not establish visual learning, robustness to new cues or currents, chosen-action reinforcement, or Sudoku ability. All summaries correctly leave `visual_level_1_passed` false.

A minimal manifest check can be rerun from the repository root using existing Python:

```python
import hashlib, json
from pathlib import Path

base = Path("experiments/level-01/004-direct-conditioning")
for name in ("probe", "probe-tonic5", "train8"):
    summary = json.loads((base / name / "summary.json").read_text())
    for file, expected in summary["files_sha256"].items():
        assert hashlib.sha256((base / name / file).read_bytes()).hexdigest() == expected
```
