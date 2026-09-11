# Development assay: unchanged Step 2 memories

This assay uses the 96-grid development family only. The 192-grid confirmation
family remains reserved. Render base, shifted, and smaller glyphs; parse every
image to verify that the full board input actually produces its recorded neural
code. Simulate each distinct frozen input once per memory condition, link all
presentation aliases explicitly, and independently validate the first accepted
digit from an unfiltered fixed scan.

Restore the four Step 2 paired snapshots and their corresponding controls from
`experiments/level-02/005-controlled-replication/train`. Use their exact template
bank, group assignment, eta, currents, global offset (1.625 Hz), and decision
deadband (2 Hz). Present the three row peers through their eight existing KC
representatives each: 24 active cells. This increases sensory drive, so transfer
may fail even though all pair associations remain present. No readout parameter
will be adjusted inside this assay, and no dopamine teaching pulse is given.

The performance and causal gates are fixed in the [Step 3 record](../README.md).
Preserve any failed result as development evidence before changing the method.

```sh
.venv/bin/python one_blank.py --split development --out experiments/level-03/001-zero-shot/development
```

## Outcome: candidate-judgment gate failed

Both training orders score 62.5% balanced accuracy in mapping 0 and 50% in
mapping 1. Acceptance recall, acceptance precision, and fixed-scan board
completion are 100%, but rejection recall is only 25% / 0%. Incorrect
candidates mostly produce timeouts. Counting successful board completion alone
would hide this failure of the declared acceptance/rejection task.

All 16 untrained neural inputs produce the same output rates at 24 active KCs.
The expanded stimulus therefore introduces an output response plateau. The
subsequent experiment will reduce the number of stimulated representatives,
without silently changing this assay's weights or decoder. All controls and
exact-erasure checks completed. The assay recorded 18,432 rendered judgments,
16 distinct neural inputs, and 528 actual neural evaluations in 70.87 seconds.
