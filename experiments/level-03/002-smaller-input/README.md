# Development: 18 sensory cells instead of 24

The unchanged transfer assay accepted the right candidate, but mostly timed
out on wrong candidates. Its untrained outputs were identical across inputs,
indicating a response plateau under the stronger 24-cell stimulus.

Use six representatives from each pair (the first three per hemisphere in the
already saved anatomy-balanced ordering), for 18 total. All pairs and positions
receive identical treatment; neither labels nor solutions select cells. Retain
the exact Step 2 weights, currents, global offset, and 2 Hz deadband. No new
training is performed. The same development family, presentation variants,
four source conditions, controls, erasure checks, and gates apply.

```sh
.venv/bin/python one_blank.py --split development --per-pair 6 --out experiments/level-03/002-smaller-input/development
```

## Outcome: improved, but still failed

Both source orders score 79.17% balanced accuracy in mapping 0 and 91.67% in
mapping 1. All valid candidates are accepted and fixed-scan completion remains
100%; rejection recall is only 58.33% / 83.33%, below the predeclared 85% floor.
Frozen/no-feedback/inconsistent controls score 29.17% / 16.67% balanced accuracy.
All memory and erasure checks pass. The complete development assay took 71.45
seconds. Reducing drive improves discrimination, but this result does not
complete the task or justify opening the held-out family.
