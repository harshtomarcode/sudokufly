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
and a visual recovery example are recorded in experiment 002. A shorter fixed
teaching schedule is the next proposed retention experiment; no Step 6 work has
started.
