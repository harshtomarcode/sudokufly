# Step 3: one-blank 4×4 Sudoku

Step 2 completed in `10b67e5` before this stage began. Project Step 3 is the
one-blank candidate task in the original research plan, not the later task
that isolates row, column, and box conflicts.

Present a full, valid 4×4 board with exactly one blank and a separate candidate
digit. Offer all four digits at every blank position. The fly must accept the
unique completing digit and reject the other three. A fixed ascending candidate
scan also measures whether its first acceptance completes the board, without
an oracle filtering or correcting a choice.

The complete domain contains 288 solved grids, 4,608 masked boards, and 18,432
candidate judgments per rendering. Full Sudoku symmetries yield only two
structural families, of 96 and 192 grids. Use the 96-grid family for development
and reserve the 192-grid family for confirmation after choices are frozen.
Verify every masked board has exactly one completion against the enumerated
solution universe. Do not split augmented versions of the same family across
development and confirmation.

The first experiment transfers all four learned Step 2 memories and their
matched frozen/no-feedback/inconsistent controls. It performs no new learning.
The image encoder locates the blank from pixels, reads its three row peers and
the candidate using the fixed template bank, and drives the same eight KC
representatives per pair used in Step 2. Three peers therefore drive 24 KCs,
compared with 16 for the earlier two-peer task. Weights, currents, timing, and
the saved global decoder initially remain unchanged.

Before seeing results, retain these gates in every mapping/order: at least 90%
balanced candidate accuracy; at least 85% acceptance recall, rejection recall,
and balanced accuracy for every candidate digit, blank position, and rendering;
at least 90% precision and one-blank completion rate; at least 25 percentage
points above each matched control; fully frozen inference, exact effective and
latent memory erasure, and unchanged nonplastic weights. Always rejecting has
75% raw accuracy but only 50% balanced accuracy and completes no boards.

Full boards are rendered, but template recognition and target-row attention
are engineered. On valid one-blank boards the row alone is sufficient. This
stage cannot distinguish row reasoning from column, box, or global-frequency
shortcuts. The 18,432 judgments collapse to 16 unordered row/candidate neural
inputs under this interface. Report that dependence explicitly, and do not
claim all-rule Sudoku reasoning, abstract symbol equality, or general puzzle
solving from this milestone.

## Development history

All listed assays transfer the same four saved Step 2 memories without new
training. Accuracy below is balanced candidate accuracy for mappings 0 / 1;
both source orders give the same aggregate values.

| Experiment | Input | Balanced accuracy | Result |
| --- | --- | --- | --- |
| [001](001-zero-shot/README.md) | 24 simultaneous KCs | 62.50% / 50.00% | Rejection timeouts; failed |
| [002](002-smaller-input/README.md) | 18 simultaneous KCs | 79.17% / 91.67% | Rejection recall below floor; failed |
| [003](003-twelve-cells/README.md) | 12 simultaneous KCs | 54.17% / 100.00% | Mapping 0 timeouts and false acceptances; failed |
| [004](004-staggered-input/README.md) | 24 KCs, fixed per-neuron onset delays | 66.67% / 79.17% | Timeouts and false acceptances; failed |
| [005](005-output-current/README.md) | 24 simultaneous KCs, output current 5.0 | 91.67% / 58.33% | Rejection recall below floor; failed |

Experiments 001–003 and 005 complete 100% of boards under the fixed ascending
scan; 004 completes 75% / 100%. None meets the explicit accept/reject gate in all
conditions. Scan completion cannot replace candidate-level evaluation.

Experiment [006](006-error-conditioning/README.md) begins task-specific training:
the paired arm receives bidirectional teaching only after wrong or undecided
judgments. Every arm starts from the same learned Step 2 memory within each
condition. It restores the original 24-cell, current 5.5 operating point and
retains the full task gate. This experiment is separate from zero-shot transfer.
Only one of its four conditions converges; the other three fail, so it does
not complete Step 3. Experiment [007](007-depression-conditioning/README.md)
tests error-contingent weakening without the additional potentiation phase.
