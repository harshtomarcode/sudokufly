# Two-epoch Undo dose probe

Experiment 002 demonstrated Undo learning but lost old conflict rejections
through passive memory decay. Preserve its source at `a3f692d` and all its
artifacts unchanged. The current source adds explicit epoch and diagnostic-arm
options; the recorded original version remains reproducible from Git.

Predeclare four paired conditions (two inherited histories × two mappings),
each with exactly two of the original balanced 30-trial epochs. Everything else
stays fixed: sensory groups, dopamine timing, currents, decoder, inherited
memories, all 121 evaluation inputs, erasures and development episodes. Every
condition runs to completion. This is a dose/retention diagnostic, not a new
control study or a full-stage pass.

Each arm exposes memories to 72 seconds of active windows, predicting a passive
u factor `exp(-72/1800) = 0.960789439`. Narrow old response margins mean that
less decay may still be insufficient. Evaluate frozen Undo recall, all 16
familiar judgments, actual placement occupancy gates and sequential recovery.
Timeouts remain errors. Retention still requires 16/16. The original occupancy
thresholds remain 90% nonempty balanced accuracy, 85% every present class at
every nonempty occupancy, and 25 points above the recorded original-history
controls. Do not compare this broad placement score with warm controls as if
a 25-point improvement were possible from their already high inherited scores.

Control-dependent Undo gates are explicitly null in this paired-only probe.
No reserved puzzles are evaluated. If retention or placement fails, preserve
the result and proceed to a separately predeclared repair experiment rather
than repeat expensive controls for a failed prerequisite.

```sh
.venv/bin/python learn_undo.py --epochs 2 --paired-only --out experiments/level-05/003-shorter-undo/development
```

## Result

Source frozen at `e42ad52`; runtime 201.73 seconds. All four conditions retain
100% Undo recall and solve 159/160 development puzzles under both policies.
Only one condition passes familiar judgment retention. Both current occupancy
gates still fail; control-dependent Undo gates remain null, not passed.

The independent [neural audit](audit-neural.json) verifies all 240 teaching
trials, 1,345 frozen evaluations, 17 full-weight checks, 121 inputs and both
erasures. The [episode audit](audit-episodes.json) verifies 1,280 episodes and
17,464 action transitions, plus 432 canonical and 96 episode encodings.
Old u/w values match the predicted 72-second passive relaxation within 4.7e-14.
Reports are [bound to the raw summary](audit-files-sha256.json).

Shorter teaching helps but does not finish retention or repair occupancy.
Proceed to a separate joint-rehearsal pilot with the existing sensory groups,
reinforcing weak placement and Undo responses through the same learning rule.
No held-out evaluation or full-stage pass is claimed.
