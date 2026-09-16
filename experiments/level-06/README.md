# Step 6: learn to defer ambiguous moves

**The first development pilot passes; Step 6 remains incomplete.** Starting
from one saved Step 5 history under both answer mappings, additional teaching
changes all 24 targeted ambiguous judgments while retaining the other 36
placement judgments and all 16 Undo judgments. Both mappings first pass at
epoch 4 and solve all 160 development boards with 512 correct placements,
zero wrong placements and zero executed Undos.

Learning stays within the same 7,835 existing synapses. The visual encoder and
binary action decoder remain fixed. A new, fixed selector compares every digit
at every empty cell and chooses the highest accepted neural score; it does not
check Sudoku legality or consult a solution. This selector is supplied by the
experiment, and its scores are not calibrated confidence.

The original memory under that same selector solves only 128/160 and 114/160
boards, with 32 and 46 wrong placements. All matched controls fail the 24 changed
judgments. This supports learning local deferral in the inherited representation.
It does not establish general search or an advantage over every earlier policy:
the favorable Step 5 warm controls already solved all 160 development boards
under the old menu by avoiding ambiguous choices.

The new policy assesses 4,480 offers across these boards, versus 2,183 total
placement/Undo offers for the old paired policy. Fewer board mistakes cost more
neural evaluations here. The default **Careful choices** demo shows four chosen
placements and exposes all 40 candidate assessments; the three Step 5 replays
remain available.

See the [prospective protocol](001-cautious-choice/README.md),
[complete results and limits](001-cautious-choice/RESULTS.md), and
[independent artifact audit](001-cautious-choice/final-audit.json).
No reserved puzzles were evaluated. This single inherited history, finite-input,
development-only pilot does not complete Step 6.
