# Step 5: sequential 4×4 Sudoku

Step 4 merged into main at `c4bbb60`. The next milestone requires the fly to
complete multi-blank puzzles through a fixed candidate scan and explicitly
accept an undo action when recovery is needed. Neither one-step judgment nor
greedy completion of easy cases is sufficient.

The first [assay](001-variable-peers/README.md) measures two prerequisites:
transfer to varying numbers of distinct peer symbols, and actual sequential
placements on easy puzzles versus puzzles where ideal local greedy choices
lead to a dead end. It uses frozen inherited memories and does not implement
undo. Its success cannot complete Step 5; its failures locate the next learning
or representation requirement.

Host mechanics may apply chosen moves and keep a visible action history. They
must not filter illegal candidates, repair choices, automatically invoke undo,
or restore per-branch retry cursors that silently supply a search algorithm.
Future undo learning needs its own visible operation/context representation
and controlled neural conditioning, followed by a separate recovery gate.
