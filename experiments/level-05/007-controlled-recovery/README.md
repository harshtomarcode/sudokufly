# Prospective controlled replay and frozen Step 5 confirmation

This protocol is fixed before running the new controls or inspecting reserved
performance. Earlier pilot failures and their gates remain in Git. A selected
pilot is exploratory; replaying its saved deterministic histories is a
controlled reproduction, not a fresh independent learning replication.

## Freeze the selected algorithm and chronology

Commit the selected pilot source, anatomy-selected occupancy banks, decoder,
teaching margins, candidate menu, stack mechanics, observation reset rules,
selected epoch for each source condition, and every cue/teaching decision.
Use the unchanged original 7,835 plastic edges and two saved Step 3 histories,
each under both answer mappings. All arms start from that condition's ORIGINAL
PAIRED STEP 3 W/u/w, before any Undo training.

Replay two fixed stages: (1) all 60 trials of the two-epoch 003 Undo schedule;
(2) every trial through the selected pilot epoch, including trials that received
no teaching. Preserve each trial's exact input, duration, reset boundary and
teaching mask. Support the selected pilot's five-phase bidirectional teaching
and, if selected prospectively, two-phase depression-only old-three-peer
teaching. Do not choose a fresh stopping epoch independently for controls.

The paired replay must exactly reproduce the saved 003 endpoint and selected
pilot endpoint W/u/w, plus comparable intermediate spike, score and memory
records. A mismatch is an implementation/provenance problem to resolve; never
substitute a more successful checkpoint. Save the full schedule before teaching.

## Matched controls

| Arm | Input chronology and teaching opportunities | Update treatment |
| --- | --- | --- |
| Paired | Exact selected replay | Correct recorded teacher, original rule |
| Frozen | Same cues, pulses, durations, resets and mask | W/u/w frozen throughout |
| No feedback | Same cues, durations, resets and mask | Omit DAN pulses; retain learning and passive-update windows |
| Inconsistent | Same cues, durations, resets and mask | Assign deterministic inconsistent targets within the enabled teaching events of each input |

For inconsistent teaching, precompute near-equal semantic 0/1 targets over ALL
enabled occurrences of each physical input, then shuffle with a recorded seed.
For an odd count, select the extra bit by a fixed seeded rule independent of
true labels and control outcomes; record which input received the extra bit.
Do not call odd counts exactly balanced. Retain 003's recorded balanced prefix
schedule separately if exact reproduction of its existing controls is desired.
Apply the answer mapping only after choosing semantic targets.

Bidirectional events still deliver each compartment once irrespective of target.
For depression-only events, a randomized target changes compartment exposure;
report actual per-compartment pulse counts/durations and this deliberate control
intervention. Do not claim identical compartment-specific dose unless verified.
All nonfrozen arms must receive equal total update-window duration, including
passive decay. Skipped paired trials stay skipped for every arm; controls never
use their own prediction to choose whether teaching occurs.

## Prospective gates, required in every history and mapping

The primary placement policy is the selected new occupancy routing. Previous
policies remain diagnostic records; they are not silently reclassified as passes.

1. **All 60 nonempty placement contexts:** balanced accuracy >=90%; each present
   class's recall at each count 1/2/3/4 >=85%; >=25 percentage points over EACH
   matched warm control on the same 60 contexts.
2. **The fixed 44 newly routed contexts, counts 1/2/4:** balanced accuracy >=90%
   and >=25 percentage points over EACH matched warm control. This subset is
   defined by the new representation, not by which inputs initially fail or
   improve. Retain count-four examples even when an untrained mapping already
   rejects them. Do not require gain separately on this single-class subgroup.
3. **Original three-peer retention:** all 16 familiar judgments remain correct.
   This is preservation of an inherited skill, with no separate gain requirement.
4. **Undo:** all 16 contexts have balanced accuracy >=90%, both class recalls
   >=85%, and >=25 percentage points over EACH warm control. This tests learning
   over the complete Undo-plus-joint continuation, not necessarily the added
   value of joint Undo rehearsal after 003.
5. **Sequential recovery:** >=90% solved in EACH existing blank-count/easy/trap
   stratum and EACH base/shift/small view, using the unchanged selected policy and menu. Never replace explicit
   rejection accuracy with next-candidate scanning success. Report controls,
   actual Undo executions and deterministic loops separately.
6. **Integrity:** frozen inference, unchanged nonplastic weights, exact initial-
   source and full-original erasure, and exact paired reproduction all pass.

Counts zero and four are single-class: report explicit acceptance and rejection
recall respectively, without fabricated balanced accuracy. Empty-peer behavior
is reported outside the nonempty gate; this exception is fixed now and does
not authorize a hardcoded acceptance or inclusion of empty contexts in claims.

Keep BOTH whole-60 and new-44 control gaps. The observed new-routing baseline
allows the original whole-placement gap to remain meaningful. If a control
later performs too well, preserve that failed causal gate; do not switch subsets.

## Erasures and interpretation

After evaluation, restore common initial Step 3 W/u/w and remeasure every
declared physical input exactly against inherited responses. Then restore the
original graph weights and zero u/w and remeasure exactly against baseline.
Hash the entire network before and after every frozen batch and at interventions.
Checkpoints, schedules, input manifests, source files and raw logs are hash-bound.
Optional joint-only ablation may restore each arm's own post-003 state; it must
be distinguished from whole-continuation erasure and cannot establish extra
joint Undo necessity when Undo was already learned during the prefix.

## Reserved-family confirmation

Only after all controlled development gates pass and all code, schedules,
memory files, results and manifests are committed, load those frozen checkpoints
for the 160 reserved puzzles. Require the same >=90% recovery gate in every
existing stratum and each of base/shift/small, matching controlled development.
Verify canonical neural responses and
all input/rendering mappings against the development records. Run no teaching,
calibration, checkpoint selection or early stopping based on reserved results.
Evaluate the same saved control arms. Full-stage completion is eligible only
after this frozen confirmation and every other gate passes.

The two board families still share the finite trained neural representations.
Confirmation establishes board/rendering coverage, not unseen-neural-pattern
generalization. Template vision, spatial attention, occupancy routing, fixed
scan order and the move stack are engineered. Success would not establish a
learned general search algorithm or independent biological replication.

## Selected pilot and execution

Select experiment 006, source `acfc3a6`, first passing epochs 3/5/3/5.
Its audited result commit is `4ee8a9c`. The new runner preserves this exact
algorithm, all four checkpoints and their full learning chronology. Use all
three views (base, shift, small) in BOTH controlled development and confirmation;
each of the fifteen stratum/view groups must independently meet the 90% gate.
Raw training, neural and episode logs are losslessly compressed for Git.

```sh
.venv/bin/python confirm_sudoku.py --pilot experiments/level-05/006-original-rehearsal/development --out experiments/level-05/007-controlled-recovery/development
# Only after controlled development passes and its artifacts are committed:
.venv/bin/python confirm_sudoku.py --pilot experiments/level-05/006-original-rehearsal/development --split heldout --development experiments/level-05/007-controlled-recovery/development --out experiments/level-05/007-controlled-recovery/heldout
```
