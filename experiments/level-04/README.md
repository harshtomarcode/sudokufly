# Step 4: isolated row, column, and box constraints

Step 3 completed before this stage; its PR merged into main at `9345490`.
Step 4 asks whether assisted candidate judgments respond to each Sudoku
constraint separately, including legal candidates that appear elsewhere on
the board. Sequential puzzle completion remains Step 5.

The first [experiment](001-frozen-transfer/README.md) transfers the original
Step 3 learned and control memories without additional teaching. It extends
engineered visual attention from the target row to the union of the target's
row, column, and box. Three distinct attended symbols preserve the existing
24-KC input and fixed decision decoder.

Four-clue boards isolate row-only, column-only, and box-only conflicts. Matched
legal cases contain the candidate digit only outside those units; swapping it
with a peer creates a conflict without changing occupied positions or the full
glyph histogram. All four candidates are offered on every board. A detector
using only two constraints reaches at most 83.33% balanced accuracy; a global
duplicate detector reaches 50%.

This restricted domain also admits a perfect outside-clue shortcut: all four
clues are distinct, so the legal candidate equals the sole outside clue. That
clue is excluded from this agent's neural input; report the shortcut anyway.

This is an assisted spatial-interface transfer experiment. Relevant geometry
is selected by code; it is not learned inside the fly. The same 16 neural
representations recur across stages and structural splits. A pass would support
this restricted four-clue task, without establishing new Step 4 learning,
variable occupancy, repeated peer symbols, or general Sudoku solving.
