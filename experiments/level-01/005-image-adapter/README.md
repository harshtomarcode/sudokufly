# Experiment 005: image-derived cue learning

**Step 1 passes under the declared engineered visual adapter.** Both opposite
assignments pass with both training orders. All four rendering conditions are
correct in every paired run. This replaces the sensory and output interfaces
for this variant; it does not repair or validate the native retinal/DNp20 assay.

## Interface and protocol

The adapter receives the actual RGB image. It finds the ink bounding box,
resamples it to 8×8 pixels, centers and normalizes the pixel vector, applies fixed
seeded random filters, and stimulates the 16 highest-response KCs. The 256-cell
candidate pool is selected from existing KCs that contact both original memory
compartments, by anatomical support. Labels and cue identities do not enter the
encoder. The task renderer and teacher know the cue identity; evaluation reads
only the image-derived stimulation and neural response.

All 166,700 neurons and 25,582,938 graph connections remain available to the
simulator. The original 7,835 KC→MBON07/11 edges can learn. The learning rule is
unchanged. The retinal input and lamina bias are zero; the new sensory adapter
bypasses native retinal processing. Each of the six MBON output cells receives
the same fixed background current of 5.5 model units. This is an engineered
visual interface, not a physiological reproduction of fly vision.

The fixed score is mean MBON11 rate minus mean MBON07 rate, minus a global
unlabelled baseline offset of 1 Hz. Thresholds are ±3.5 Hz. These were fixed by
the untrained probe, using its two raw scores of +3.5 and −1.5 Hz and a deadband
covering both. There is no per-image correction or trained output classifier.

Each run presents eight examples of each cue (16 trials total), with two
different training orders and both opposite valence assignments. Only the
original rendering is trained. Cue presentation lasts 500 ms with weights
frozen and eligibility traces active. A 200-ms cue-off DAN pulse enables local
plasticity; 250 ms then allows passive consolidation with associative updates
disabled. Feedback pairs each cue with its assigned valence, independently of
the decoded action. This is supervised association through dopamine stimulation.

## Held-rendering results

| Assignment | Order | Paired | Frozen | No feedback | Inconsistent pairing |
|---|---|---:|---:|---:|---:|
| Vertical accept / horizontal reject | 20260911 | 100% | 12.5% | 12.5% | 0% |
| Horizontal accept / vertical reject | 20260911 | 100% | 0% | 0% | 12.5% |
| Vertical accept / horizontal reject | 20260912 | 100% | 12.5% | 12.5% | 0% |
| Horizontal accept / vertical reject | 20260912 | 100% | 0% | 0% | 0% |

Each accuracy uses both cues in four views: original, shifted, thinner bars,
and thicker bars. Thus there are 32 paired test presentations across four
trained states. Every paired view is correct. Controls mostly time out; their
low accuracy should not be described as below-chance forced classification.

Shifts normalize to the same KC pattern by construction. Thin/thick bars
retain 13–15 of the original 16 selected KCs, so they test a changed neural
input rather than merely another pixel arrangement with the identical code.
The adapter builds translation normalization in; the fly does not learn it.

Paired runs change 60 or 56 connections depending on the assignment. Frozen
and no-feedback runs change zero; inconsistent pairing changes 112. No paired
efficacy reaches a bound. Every erasure evaluation recovers the complete
baseline spike-count hashes. All nonplastic weights remain unchanged.

These results establish small visual cue association under the specified
adapter, readout, resets, and teaching windows. They do not establish natural
retinal recognition, chosen-action learning, or symbol comparison. Step 2 must
have its own split and gates. Two deterministic training orders and engineered
render variations do not provide broad biological or statistical replication.

## Reproduction

Use the source version committed with this experiment:

```sh
.venv/bin/python compare_symbols.py probe --task cues --out runs/image-cue-probe
.venv/bin/python compare_symbols.py train --task cues --reference runs/image-cue-probe --out runs/image-cue-train
```

The [probe](probe/summary.json) precedes training. The [training protocol](train/protocol.json)
and [input manifest](train/inputs.json) bind parameters, source hashes, images,
and selected neuron IDs. The [summary](train/summary.json) hashes all training
artifacts, including 16 memory-only snapshots. Raw trial records include neural
counts, fixed-decoder scores, and effective/latent memory hashes. The independent
[audit](audit.md) reviews the completion evidence and claim limits.
