# Step 2 development: centered random visual features

Step 1 was completed and committed in `530c0be` before this experiment.
This is the first neural symbol-comparison development run. No result is
assumed in advance. Source and inputs are bound by each protocol's SHA-256.

Train all 16 ordered single-row-symbol/candidate pairs over digits 1–4 in
base and bold rendering. Repeat each matching pair three times per epoch,
giving balanced valence exposure. Test all 48 ordered two-distinct-symbol
rows with each candidate, in base, shifted, smaller, and bold rendering.
Every two-cell composition is absent from training; bold is a trained style.
Shift invariance and pooling over row slots are engineered. This is familiar
symbol composition, not novel-symbol equality or Sudoku reasoning.

The fixed encoder subtracts the uniformly weighted training-patch mean before
independent seeded random candidate/row projections, rectifies their products,
max-pools row evidence, and selects eight existing KCs per hemisphere. Labels
do not enter it. Eta is reduced from 0.001 to 0.00025 because shared features
otherwise receive many more dopamine pairings than the Step 1 cue patterns.
The untrained probe fixes one global output offset and deadband. No readout
parameter is fitted using reinforced responses.

Before training, the gate is fixed at ≥90% balanced accuracy in both opposite
valence mappings and both orders; ≥85% for each class, candidate, and view;
≥25 percentage points above frozen, no-feedback, and inconsistent controls.
Each inconsistent case/style receives equal reward and aversive pulses.
Erasure must recover every baseline spike-count hash exactly and all
nonplastic weights must remain unchanged.

An idealized count-only assessment of random features is development evidence,
not fly learning. It predicted an unresolved candidate-specific weakness.
Any subsequent representation selection using these outcomes must remain
explicitly exploratory and be followed by fresh fixed-protocol replication.

```sh
.venv/bin/python compare_symbols.py probe --task symbols --eta 0.00025 --out experiments/level-02/001-centered-features/probe
.venv/bin/python compare_symbols.py train --task symbols --eta 0.00025 --reference experiments/level-02/001-centered-features/probe --out experiments/level-02/001-centered-features/train
```

## Outcome: failed development run

The first paired run (order 20260911, mapping 0) scored **60/192 = 31.25%**,
with 132 timeouts. Both base and shifted scored 29.17%, smaller 25%, bold
41.67%. It changed 526 existing synapses; minimum efficacy was about 0.1001,
close to the lower bound despite reducing eta. All 192 erased spike-count
hashes recovered baseline exactly. Nonplastic preservation was checked by the
runner before erasure. The probe selected offset 1.09375 Hz and deadband
5.90625 Hz. A post-hoc zero-deadband diagnostic only reached 76.04%; changing
the threshold alone cannot rescue this representation.

The run was interrupted during frozen-control training after this completed
paired failure, since the all-runs gate was already impossible. Remaining
controls, opposite mapping, and second order were not completed. Raw partial
trials, the paired memory snapshot, inputs, protocols, and an explicitly
partial summary are retained. This is not a completed controlled success.
