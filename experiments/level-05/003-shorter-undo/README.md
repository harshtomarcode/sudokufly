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
