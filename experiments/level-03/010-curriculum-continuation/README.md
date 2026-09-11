# Controlled Step 2 → Step 3 curriculum continuation

Experiment 007 demonstrates perfect paired one-blank judgments in all four
conditions, but its warm-start shuffled controls perform too well to establish
the necessity of correct EXTRA Step 3 feedback. That experiment remains failed
for its stated causal question. Common calibration experiments 008–009 also
remain failed; their results are not substituted into this experiment.

This continuation asks whether the successful behavior depends on learning
across the curriculum. Restore each ORIGINAL Step 2 arm's own W/u/w, rather
than giving all arms the paired memory. Then run exactly 007's eight-epoch,
error-contingent depression-only protocol: paired receives correct teaching
only after wrong/undecided judgments; frozen and no-feedback replay its events
under their respective update restrictions; inconsistent continues from its
own source and receives the same declared shuffled event schedule.

The paired starting states, cue order, learning rule, and teaching events are
unchanged. Require their training traces, final W/u/w, and frozen decisions to
reproduce 007 exactly. Step 2 histories are restored, not freshly retrained.
Controls compare the whole curriculum; they cannot isolate the extra value of
correct Step 3 pairing, which is addressed by 007's retained warm-start audit.

All numerical gates remain unchanged: balanced accuracy ≥90%; both class recalls
and all digit/blank/view balanced accuracies ≥85%; precision and completion ≥90%;
≥25 percentage points over EACH curriculum control; fully frozen inference,
exact own-source and full memory erasure, and unchanged nonplastic weights.
Use the original 24 simultaneous KCs, current 30, output current 5.5, eta0.00075,
1.625 Hz offset, and 2 Hz deadband. No calibration rounds or other changes apply.

After all four development conditions pass and their code/parameters/states are
committed, evaluate all 192 reserved grids, 16 blanks, four candidates and three
views with frozen snapshots. Do not retrain or tune from confirmation outcomes.
The board families alias the same 16 representations; successful confirmation
shows full board/rendering coverage, not novel neural generalization. A pass
would complete the assisted one-blank behavioral milestone, not prove a newly
learned Sudoku rule or that correct extra board-labelled feedback was necessary.

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --train-epochs 8 --teaching depression --control-history curriculum --out experiments/level-03/010-curriculum-continuation/development
# Only after all development gates pass and snapshots/source are committed:
.venv/bin/python one_blank.py --split heldout --per-pair 8 --timing simultaneous --teaching depression --control-history curriculum --conditioning-source experiments/level-03/010-curriculum-continuation/development --out experiments/level-03/010-curriculum-continuation/heldout
```
