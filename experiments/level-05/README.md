# Step 5: sequential 4×4 Sudoku

**Complete for the restricted assisted task:** controlled learning, familiar
memory retention, frozen reserved-family recovery and selective Undo-memory
erasure all pass. The task uses 4×4 puzzles with 2–4 blanks, a fixed candidate
scan and an explicitly offered Undo action. Step 6 has not started.

## Final result

Each result holds for both saved training histories, both answer mappings and
all three renderings. There are 160 distinct development puzzles and 160 distinct
reserved puzzles; repeated histories, arms and views are not independent boards.

| Measurement | Development | Reserved, no new learning |
| --- | --- | --- |
| Nonempty placement judgments | 60/60 correct | 60/60 correct |
| Newly routed placement judgments | 44/44 correct | 44/44 correct |
| Familiar three-peer judgments | 16/16 retained | 16/16 retained |
| Undo judgments | 16/16 correct | 16/16 correct |
| Complete puzzles | 159/160 (99.38%) | 158/160 (98.75%) |
| Predefined traps | 63/64 (98.44%) | 62/64 (96.88%) |
| Weakest puzzle stratum, each view | 31/32 (96.88%) | 30/32 (93.75%) |

The smallest balanced-accuracy gains over any matched warm control are 42.19
percentage points on the whole nonempty placement task, 51.25 points on the
44 new contexts and 50 points on Undo. Empty-peer inputs remain silent and
outside the nonempty gate, as declared before these experiments.

The [controlled reproduction and confirmation](007-controlled-recovery/README.md)
replays the selected learning histories exactly, then evaluates committed
memories on the reserved family with no training or parameter changes. Its
audits independently verify neural responses, memory preservation, puzzle
construction, rendered inputs, every recorded action and every declared gate.
Reserved results are committed at `e017e0e`.

## What the controls establish

| Answer mapping, both histories | Learned development | Each warm control, development | Learned reserved | Each warm control, reserved |
| --- | --- | --- | --- | --- |
| 0 | 159/160 | 160/160 | 158/160 | 160/160 |
| 1 | 159/160 | 44/160 | 158/160 | 50/160 |

The warm controls start with the same learned Step 3 placement memory. Their
low explicit judgment accuracy does not prevent useful behavior: mapping-0
controls reject ambiguous offers and revisit cells on later sweeps, solving all
boards without Undo. The trained policy accepts locally legal ambiguous moves,
then sometimes needs Undo. A "trap" means a trap for the ascending first-legal
scan used to define the dataset, not a puzzle proven to require backtracking.

New association learning and robustness across answer mappings are demonstrated.
Higher puzzle completion than every control, and a general need for new learning
or Undo to complete these puzzles, are not established.

The prospectively added [selective-erasure assay](008-selective-undo-erasure/README.md)
isolates Undo's contribution **within the trained placement policy**. It restores
only the 892 anatomically selected Undo-associated edges and their latent memory
to the original pretraining state. The remaining 6,943 plastic edges, all
nonplastic weights and all 149 placement responses stay unchanged.

| Answer mapping, both histories | Intact reserved traps | Undo-erased reserved traps | Solve-rate loss |
| --- | --- | --- | --- |
| 0 | 62/64 | 0/64 | 96.88 percentage points |
| 1 | 62/64 | 15/64 | 73.44 percentage points |

Every view passes the predeclared 25-point effect threshold. Restoring the
trained memory reproduces all 165 neural responses exactly. The denominator
includes every predefined trap, including the two original failures. Both
development and reserved selective-erasure audits pass; the final reserved
result is committed at `cfabc8c`. This intervention restores old Undo responses;
it does not simply disable the Undo action or change the placement policy.

## Experiment history

Every failed pilot and its original gates remain recorded in Git.

| Experiment | Finding |
| --- | --- |
| [001: variable peers](001-variable-peers/README.md) | Inherited memory solves easy cases but no traps; broader placement judgments fail. |
| [002: learned Undo](002-learned-undo/README.md) | New Undo learning and 159/160 recovery pass, but passive decay damages familiar memory. |
| [003: shorter Undo](003-shorter-undo/README.md) | Two epochs preserve perfect Undo with less decay; only one of four conditions retains all familiar judgments. |
| [004: joint rehearsal](004-joint-rehearsal/README.md) | Shared-input rehearsal fails retention and recovery; only 8/640 repeated episodes solve. |
| [005: occupancy banks](005-occupancy-banks/README.md) | Separate sensory routes learn all 44 new judgments, but familiar retention still fails; 13/640 repeated episodes solve. |
| [006: original correction](006-original-rehearsal/README.md) | The original error-triggered correction restores retention; all four pilots pass at epoch 3 or 5. |
| [007: controlled recovery](007-controlled-recovery/README.md) | Matched controls demonstrate new judgment learning; unchanged memories pass reserved-family confirmation. |
| [008: selective Undo erasure](008-selective-undo-erasure/README.md) | Removing only Undo memory reduces recovery with placement fixed, in development and reserved families. |

The successful adjustment combines separate sensory routes for peer counts
1, 2 and 4 with the original correction rule for familiar three-peer judgments.
Correct familiar judgments receive no teaching; errors receive the shorter
depression-only correction. Only seven familiar corrections are needed across
the four selected runs. New placement and Undo associations use bidirectional
conditioning. Learning remains within the original 7,835 existing KC→MBON07/11
connections; no trained output layer, new neurons or new connections are added.

## Scope and remaining failure

Template recognition, spatial attention, occupancy routing, the 16 Undo context
codes, candidate order and the move stack are engineered. The host applies
neural choices; it does not filter illegal candidates, repair choices,
automatically trigger Undo or provide a per-branch retry cursor. Electrical
state resets between observations. Measured frozen responses are reused for
identical finite neural inputs during episode replay.

The reserved family is disjoint at the completed-board family level, but its
observations reuse the trained finite representations. This establishes assisted
board and rendering coverage, not unseen-neural-pattern generalization, native
vision, an advantage from fly wiring, or general Sudoku search. The two saved
histories are deterministic continuations, not independent biological replicas.

One development board and two reserved boards deterministically loop. In both
reserved failures, the policy places 1 then 3, removes both placements through
Undo, and returns to the initial board and stack. It has no new branch-history
signal to change the next attempt. The failure records remain intact; the
predeclared requirement was at least 90% solved in each stratum and view.

Reproduction commands, frozen source hashes, checkpoints, compressed raw
records, independent audit reports and their checksum manifests are linked in
the individual experiment records above.
