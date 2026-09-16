# Step 6 pilot: learn when to place and when to defer

Prospective development-only protocol. Start from Step 5's paired seed 20260919
checkpoint under both answer mappings. Retain the same sensory encoder, 7,835
existing plastic synapses, dopamine learning rule and fixed binary decoder.
Do not alter any Step 5 source, checkpoint or result.

Teach Place only when the candidate is absent from three distinct peer symbols;
otherwise teach Defer. This changes 24 nonempty judgments at peer counts one and
two. All 36 other nonempty placement judgments and all 16 Undo judgments must
remain correct. Empty-peer inputs remain silent and outside learning claims.
This learns local caution in an engineered representation, not whole-board
planning, visual recognition or an external trained output layer.

The fixed selector evaluates every digit at every currently empty cell, then
commits the accepted offer with greatest mapping-oriented neural readout score.
Ties use row-major cell order, then ascending digit. It recomputes after each
placement and stops if no offer is accepted. No legality mask, solution, peer
count, singleton test or teacher label enters selection. There is no automatic
Undo or fallback guessing; Undo is retained and probed separately. The rate
score is not a calibrated confidence. All offers count toward the 1,024-offer
budget, including rejected offers; fewer board mistakes may cost more neural
evaluations.

Use the existing joint-teaching rule: once per context per epoch, a frozen
500 ms observation; bidirectional teaching below a 3 Hz signed margin. Original
three-peer contexts instead receive depression-only correction when wrong or
undecided. Preserve the existing phase durations and passive relaxation during
unfrozen windows. Fix eight seeded training orders before learning; stop at the
first epoch with all 76 judgments correct and all 160 development boards solved
without wrong placements, or after eight epochs. Record all attempted epochs.

Every arm starts from the same Step 5 paired memory. Frozen, no-feedback and
inconsistent-feedback controls replay the selected paired schedule, including
its teaching mask, phase durations and reset boundaries. Inconsistent targets
are balanced per physical input over enabled occurrences, with a seeded random
extra bit for odd counts. Save those targets before control execution. Report
actual per-compartment teaching doses; frozen windows preserve weights and both
latent memory arrays. Restore initial Step 5 memory and reproduce all 165
responses exactly. All nonplastic weights must remain unchanged.

Report changed 24/24, unchanged 36/36, forced-positive 4/4, Undo 16/16, solve
counts, wrong placements, all offered candidates and failure cases for every
arm. The prespecified learning contrast balances the 24 changed negative
contexts against the four forced positives; require at least a 25-point
balanced-accuracy gain over every matched control. This contrast avoids the
full task's 4-positive/56-negative imbalance; all subgroup counts remain visible.
Never claim a gain from ranking alone: compare the original memory under the
same selector, as well as the previously recorded ascending-policy baseline.

The source ascending policy solved 159/160 development boards with 64 wrong
placements and 65 Undo operations. Before teaching, an independent frozen
replay of the new selector solved 128/160 (mapping 0) and 114/160 (mapping 1),
with 32 and 46 wrong placements. These are development observations, not
reserved results or promises of learning success. All 160 development puzzles
can be completed by the ideal forced-only target. No reserved evaluations occur
in this pilot; passing does not complete Step 6.

```sh
.venv/bin/python prioritize_sudoku.py --out experiments/level-06/001-cautious-choice/development
```

Commit this protocol and its runner before execution. Export any improved demo
from its recorded decisions and actual spike traces, identifying it as a
development pilot and preserving the original Step 5 replays.
