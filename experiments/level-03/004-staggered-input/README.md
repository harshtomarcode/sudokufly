# Development: stagger sensory onset

Population-size changes fail to transfer robustly across both action mappings.
Test artificial synchrony as a downstream bottleneck using the original 24 KCs.
Each neuron receives current 30 from a fixed onset until 500 ms. Its onset is
4 times the first SHA256 byte of its decimal neuron ID modulo 8, giving 0–28 ms.
This rule knows neither symbols nor labels. Keep saved memories, uniform MBON
current, output coefficients, offset, threshold, and all task gates unchanged.

Record selected KC and individual MBON counts in 4 ms bins through 100 ms,
then 10 ms bins to 500 ms, decoding only the summed output. First run a
simultaneous control under identical segmentation and confirm it reproduces
experiment 001. Then run staggering. The held-out family remains reserved.
This tests a timing intervention, not new training or an intrinsic firing ceiling.

The delays are fixed per neuron, with no direct symbol or label lookup. Different
symbol-selected groups can nevertheless have different delay distributions.
Delayed cells also receive slightly less total current exposure (472–500 ms),
so the intervention changes both timing and exposure.

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --out experiments/level-03/004-staggered-input/simultaneous
.venv/bin/python one_blank.py --split development --per-pair 8 --timing staggered --out experiments/level-03/004-staggered-input/development
```

## Outcome: failed

The segmented simultaneous control reproduces every one of experiment 001's
528 full-network spike-count hashes and scores exactly. In its first 100 ms,
all 24 selected KCs fire together in each of three 4 ms bins.
Staggering gives 66.67% / 79.17% balanced accuracy, 75% / 100% scan completion,
and still fails the unchanged gates in both source orders. All frozen-memory,
nonplastic, and erasure checks pass. Runtimes were 80.12 / 80.46 seconds.
Synchrony is present in the original stimulation, but this intervention does
not establish that it is the sole cause of failed transfer.
