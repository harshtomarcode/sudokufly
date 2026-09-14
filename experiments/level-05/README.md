# Step 5: sequential 4×4 Sudoku

Step 4 merged into main at `c4bbb60`. The next milestone requires the fly to
complete multi-blank puzzles through a fixed candidate scan and explicitly
accept an undo action when recovery is needed. Neither one-step judgment nor
greedy completion of easy cases is sufficient.

The first [assay](001-variable-peers/README.md) measured two prerequisites:
transfer to varying numbers of distinct peer symbols, and actual sequential
placements on easy puzzles versus puzzles where ideal local greedy choices
lead to a dead end. It uses frozen inherited memories and does not implement
undo. Its success cannot complete Step 5; its failures locate the next learning
or representation requirement.

Host mechanics may apply chosen moves and keep a visible action history. They
must not filter illegal candidates, repair choices, automatically invoke undo,
or restore per-branch retry cursors that silently supply a search algorithm.
Undo learning uses its own visible operation/context representation and
controlled neural conditioning, followed by a separate recovery gate.

The baseline is complete: paired memories solved all sampled easy cases and
none of the traps, and both occupancy policies failed their gates. The
[controlled Undo experiment](002-learned-undo/README.md) trained new associations
from the same learned starting memory in every control arm, and tested retention
and recovery separately. Its 16 context codes are explicitly engineered;
successful recall does not establish a learned general search algorithm.

**New Undo learning passes:** every paired history/mapping scores 100% versus
0–23.33% balanced accuracy in warm controls. Both placement policies solve
159/160 development puzzles, including 63/64 traps, in every paired condition.
The remaining puzzle deterministically loops. This is repeated evaluation of
the same 160 puzzles, not 1,280 independent test cases.

**Step 5 remains incomplete.** Passive decay weakens old memories during new
training, turning 4–11 familiar conflict rejections into timeouts. All paired
conditions fail the predeclared retention gate. The broader placement failures
from 001 remain unresolved and the reserved-family confirmation was not run.
The complete source, controls, checkpoints, action histories, independent audits
and a visual recovery example are recorded in experiment 002. No Step 6 work has
started.

## Retention and placement repair

The [two-epoch dose probe](003-shorter-undo/README.md) preserved perfect Undo
recall and 159/160 recovery with much less passive decay. It retained all 16
familiar judgments in only one of four conditions, and every broad placement
gate still failed. Shortening training alone was insufficient.

The [joint rehearsal pilot](004-joint-rehearsal/README.md) practiced placement
and Undo together for eight epochs. All four conditions failed: familiar
retention ended at 12/16, 13/16, 10/16 and 13/16, while Undo remained perfect.
Only 8 of 640 development episodes solved. These are repeated runs of the same
160 puzzles. Its complete failed checkpoints and independent audit are retained.

The [sensory routing pilot](005-occupancy-banks/README.md) separated inputs
for different observed peer counts while leaving familiar three-peer and Undo
inputs intact. All 44 newly routed judgments became correct in every condition,
but familiar retention failed and only 13/640 repeated development episodes
solved. New learning had to coexist with the inherited skill.

The [original correction method](006-original-rehearsal/README.md) resolves
that pilot failure. Correct familiar judgments receive no teaching; errors get
the original shorter depression-only correction. Every condition first passes
at epoch 3 or 5, with all 60 nonempty placement judgments correct, 16/16 familiar
judgments retained, perfect Undo, and 159/160 development puzzles solved.
Only seven familiar corrections are needed across the four conditions.

These are development results: neither a selected checkpoint nor a successful
recovery score alone completes the stage. The [controlled reproduction and
confirmation](007-controlled-recovery/README.md) must satisfy the prospective
learning gaps and evaluate the reserved puzzles with committed frozen memories.
Strict familiar retention, explicit placement accuracy, controlled learning
and reserved-family confirmation must all pass.
