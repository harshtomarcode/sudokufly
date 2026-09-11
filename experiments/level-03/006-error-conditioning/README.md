# Development: error-contingent internal synaptic conditioning

The five transfer variants fail the full judgment gate. Now teach Step 3 directly,
without changing the fixed pixel encoder, original 24 simultaneous KC inputs,
KC current 30, MBON current 5.5, offset 1.625 Hz or 2 Hz deadband. The unchanged local
rule and original 7,835 plastic edges remain the only learning mechanism.

Each of the four source order/mapping conditions starts from its saved paired
Step 2 memory. All four arms within a condition start from that same W/u/w.
Present 16 unique neural inputs derived from development board images. Each of
8 fixed epochs has 24 trials: each of 4 accept inputs appears 3 times and each of
12 reject inputs once; independently shuffle using source seed+1000+100*epoch.
Reset electrical state and traces between trials while preserving memory.

The paired arm first judges the image with frozen weights. Only an incorrect or
undecided judgment triggers the existing bidirectional teaching sequence:
cue 500 ms then target DAN 200 ms learning, 250 ms passive; reset electrical state;
opposite DAN 200 ms frozen, same cue 500 ms learning, 250 ms passive. Both DAN pulses
use current 20. A correct trial ends after its frozen 500 ms judgment. This is
supervised error-contingent conditioning, not an externally trained policy.

Frozen and no-feedback controls replay the paired arm's exact teaching events.
The inconsistent control permutes all 192 events (including no-teaching events)
across the identical cue schedule. This preserves total event and target-timing
counts but changes which inputs and trials receive teaching; it is not a control
with the same active windows. Reject an unchanged permutation. All controls
retain the same total cue/phase counts. No-feedback allows passive drift of
inherited memory; frozen must remain identical to inherited memory.

All judgment, subgroup, precision, completion and 25 percentage-point control
advantage gates remain. At this operating point inherited balanced accuracy
is 62.5% / 50%, so that advantage remains feasible. Eight epochs are fixed in
advance; no early stopping or selected intermediate checkpoint. Log every
judgment, teaching event, phase, memory change and final snapshot. Stage erasure
must restore inherited W/u/w and responses exactly; full erasure must restore
untrained responses and preserve all nonplastic edges.

The structural held-out family remains reserved. If development passes, freeze
code/parameters/memories and render all 192 held-out grids. Both families collapse
to the same 16 neural representations, now explicitly used in training: this
confirmation tests board rendering/coverage, not novel neural representations.

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --train-epochs 8 --out experiments/level-03/006-error-conditioning/development
# Only after all development gates pass and the source is frozen:
.venv/bin/python one_blank.py --split heldout --per-pair 8 --timing simultaneous --conditioning-source experiments/level-03/006-error-conditioning/development --out experiments/level-03/006-error-conditioning/heldout
```

## Outcome: one condition converges, three fail

| Source order | Mapping | Paired balanced accuracy | Frozen / no feedback | Inconsistent | Paired completion |
| --- | --- | --- | --- | --- | --- |
| 20260919 | 0 | 100.00% | 62.50% | 50.00% | 100% |
| 20260919 | 1 | 33.33% | 50.00% | 37.50% | 50% |
| 20260920 | 0 | 54.17% | 62.50% | 45.83% | 50% |
| 20260920 | 1 | 33.33% | 50.00% | 37.50% | 50% |

The overall gate fails. The first condition needs only 13 teaching events and
then completes six epochs without another error. Other conditions deteriorate;
the first order's mapping 1 needs 129 teaching events and reaches 21 errors in
its final 24-trial epoch. Transient lower-bound clipping occurs during training,
even though final effective weights can sit slightly above the bound after
passive relaxation. Both erasures and nonplastic preservation pass. The full
assay takes 491.38 seconds. The held-out family remains reserved.

This establishes additional internal synaptic learning, including harmful
interference, rather than reliable Step 3 behavior. See the independent audit
for the comparison against passive drift and the event-shuffling checks.
