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

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --out experiments/level-03/004-staggered-input/simultaneous
.venv/bin/python one_blank.py --split development --per-pair 8 --timing staggered --out experiments/level-03/004-staggered-input/development
```
