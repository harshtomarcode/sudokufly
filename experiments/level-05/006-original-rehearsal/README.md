# Restore the original three-peer correction method

This development experiment changes only correction of the original three-peer
placement inputs. It retains experiment 005's separate sensory banks, inherited
short-Undo memories, fixed decoder and other teaching rules. Freeze this protocol
and source before running; preserve every attempted checkpoint and outcome.

## Motivation and existing evidence

Step 3's balanced bidirectional teaching experiment 006 failed three of four
conditions. Removing its potentiating half in experiment 007 produced perfect
paired judgments in all four conditions. Step 3 experiment 010 reproduced those
paired traces and memories exactly. Actual learning required only 5, 18, 5, 17
corrective DAN pulses across the four conditions, all on conflicting contexts
within the first two epochs. Its warm-control limitation remains unchanged:
correct additional Step 3 feedback was not shown necessary.

Step 5 experiment 004 instead delivered 78, 67, 87, 69 three-peer bidirectional
teaching events. Of these, 26, 44, 26, 43 were triggered by the additional 3 Hz margin
after already correct judgments. Familiar legal judgments often became timeouts.
This motivates restoring the successful correction method for the old skill.

Experiment 005, frozen at `075367c`, completed all eight epochs in all four conditions and failed
its pilot gate. At the final checkpoints, all 44 new one-, two- and four-peer
contexts were correct in every condition, and Undo balanced accuracy remained
100%. Familiar three-peer judgments retained only 12/16, 13/16, 13/16 and 13/16
correct decisions, in history/mapping order (20260919,0), (20260919,1),
(20260920,0), (20260920,1). Final recovery solved only 4/160, 4/160, 1/160 and
4/160 development puzzles respectively. Correct new occupancy judgments therefore
did not compensate for losing the old skill. Its 7,425 frozen evaluations and
853.22-second run are preserved in the experiment 005 raw summary. These are
repeated deterministic conditions, not independent biological samples.

## Predeclared intervention

Restore the same four paired memories from
`experiments/level-05/003-shorter-undo/development` used to start 005. Select the
same disjoint anatomy-only sensory banks for one, two and four distinct peers;
three-peer inputs retain their original KCs, Undo retains its existing bank,
and empty placement context remains silent. No new anatomical edges are added.

Each epoch still presents the same 76 distinct contexts once each:60 nonempty
placement contexts and 16 Undo contexts, in the same saved seeded order. Change
only the correction protocol for original three-peer placement inputs:

1. Observe the cue for 500 ms with frozen memory.
2. If the fixed decoder's action is wrong or undecided, deliver the target DAN
   pulse for 200 ms with learning, then 250 ms passive relaxation.
3. Omit the opposite-DAN pulse, potentiating cue and second passive phase.
4. Correct judgments stay fully frozen, even below the general 3 Hz teaching margin.

Other occupancies and Undo retain the 3 Hz margin-triggered bidirectional teaching
rule. Keep KC current 30, MBON current 5.5, DAN current 20, eta 0.00075, 500 ms frozen
observation, offset 1.625 Hz and thresholds ±2 Hz. Teaching labels select dopamine
timing only; they do not enter the sensory encoder or episode decisions.

The historical reference is
`experiments/level-03/010-curriculum-continuation/development/protocol.json`
(SHA-256 `a49e2d2a6d7a09a2caa029242f748991d206ec5ea9021220d2c98022acb88f8a`),
with `one_blank.py` at commit `b165e38ca3ac2178839192e8e780cbff0256813c`
(SHA-256 `f3b1b52c3c0ff0a5c0f19fe7449f218fb5d0f4c3dc1b639071a73eacf6cd4611`).
The new run records these source and protocol references explicitly.

This restores the historical correction method, not its complete cue schedule:
Step 3 presented each legal three-peer context three times and each conflicting
context once. The present narrow intervention keeps one presentation per context.
It also changes both the correction trigger and strengthening phase, reducing
active memory time per corrected three-peer cue from 1.20 to 0.45 seconds. It
cannot separately identify the effect of those changes.

## Measurements and stopping rule

Use both saved histories and both mappings. Evaluate all 165 physical inputs
from electrical reset with frozen weights and latent memory at inheritance and
after each epoch. Compare the original 121 inherited responses exactly with 003;
measure the 44 new input references directly. Save every attempted epoch memory.
Report both old placement policies as diagnostics and the separate-occupancy
policy as primary. Verify complete network-weight hashes across frozen batches,
unchanged nonplastic weights, and exact inherited/full erasures.

The primary pilot gate requires nonempty placement balanced accuracy ≥90%,
recall ≥85% for each present class at each nonempty occupancy, all 16 familiar
judgments correct, and Undo balanced accuracy ≥90% with each class recall ≥85%.
Four-peer rejection therefore requires 4/4 correct. Timeouts remain errors.

When judgment gates pass, run the unchanged neural-placement/Undo driver on
all 160 development puzzles. Require ≥90% solved in every available blank-count
and easy/trap stratum. Stop each condition at its first joint judgment-and-recovery
pass or after eight epochs. Preserve every attempted checkpoint and failed case;
also run development episodes at the final epoch if the judgment gate never passes.

There are no new warm controls or reserved-family evaluations in this pilot.
Control gains for the new representation remain unassessed. A passing development
checkpoint requires subsequent controlled reproduction and reserved confirmation;
it cannot itself complete Step 5. All original limitations concerning engineered
vision, attention, menu and stack, trained contexts, and repeated deterministic
source histories remain applicable.

```sh
.venv/bin/python joint_sudoku.py --separate-occupancies --old-n3-depression --source experiments/level-05/003-shorter-undo/development --epochs 8 --margin-hz 3 --out experiments/level-05/006-original-rehearsal/development
```
