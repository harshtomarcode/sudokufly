# Frozen Step 3 transfer to isolated Sudoku constraints

## Declared experiment

Use all four learned Step 3 memories and their own frozen, no-feedback, and
inconsistent histories from `level-03/010-curriculum-continuation/development`.
The completed reserved-board confirmation is also verified before starting.
All weights and latent memory remain frozen: this experiment performs no new
training and tests transfer of the existing learning history.

The interface reads rendered pixels, locates the highlighted empty target,
and attends to the seven unique cells in its row, column, or box. Each occupied
peer and candidate enters the existing independently permuted template banks
and generic Cartesian pair routing. The encoder receives no labels, target
coordinates, equality flags, candidate filtering, or solver output. Geometry,
symbol recognition and attention are engineered and explicitly part of the
assisted interface.

There are exactly three occupied target peers with distinct digits: one
row-only, one column-only, and one box-only. A fourth distinct clue lies outside
all target units. Every digit appears exactly once globally, so a global
duplicate detector rejects all legal cases too. For each legal candidate,
swapping its outside clue with a peer creates a matched isolated violation
with the same candidate, occupied cells and full glyph histogram.
This restricted domain also permits a perfect outside-clue shortcut because
all four clues are distinct. The implemented encoder excludes that clue.

## Dataset and split, fixed before neural evaluation

Enumerate all 512 target/occupied layouts and all 24 assignments of four distinct
digits. Canonicalize the target and occupied positions under all 128 geometric
Sudoku symmetries, ignoring candidate and digit identity. There are five orbits.
Verify completion counts against the entire 288-grid solution universe; remove
the 64-layout orbit whose partial boards have no completion. This filter is
part of dataset construction, never neural encoding. Labels independently grade
immediate row/column/box violations; they do not select a hidden solution.

| Canonical geometry | Layouts | Completions per board | Split |
| --- | ---: | ---: | --- |
| `(0,2,5,6,8)` | 128 | 2 | Development |
| `(0,2,5,7,8)` | 128 | 1 | Development |
| `(0,2,5,8,10)` | 64 | 0 | Excluded |
| `(0,2,5,8,11)` | 128 | 1 | Held out |
| `(0,2,5,8,15)` | 64 | 1 | Held out |

Each geometry includes all digit assignments, four candidates, and the base,
shifted and smaller-glyph views. Development contains 6,144 marked boards and
73,728 candidate presentations. Confirmation contains 4,608 marked boards and
55,296 presentations. Every candidate, target and view is covered in each
split; each outcome kind has equal frequency. Binary labels have a 1:3
accept/reject ratio. All splits share exactly 16 familiar neural inputs.
The 10,752 marked board/target cases correspond to 8,064 unique underlying
partial grids: 6,144 development and 1,920 held out. Neither exact underlying
grids nor their geometry symmetry orbits cross the split.

## Fixed neural protocol and gates

Use 24 simultaneous KCs (eight per pair), current 30, uniform MBON current 5.5,
500 ms observation, and the unchanged `MBON11 - MBON07 - 1.625 Hz` score.
The fixed +/-2 Hz deadband produces two actions or timeout; timeout is wrong.
Each inference resets electrical state while retaining frozen W/u/w. No
dopamine teaching or passive memory relaxation occurs. The full graph and
original 7,835 plastic-edge identities remain unchanged.

Every source order and answer mapping must meet all gates:

- Balanced accuracy at least 90%, precision at least 90%.
- Legal acceptance recall and each isolated constraint's rejection recall at
  least 85%; candidate/target/view balanced accuracies at least 85%.
- At least 85% correct on both members of each constraint's matched swap pairs.
- At least 25 percentage points above each original-history control.
- Frozen effective and latent memory, exact full erasure, unchanged nonplastic
  weights, and verified source/artifact hashes.

Report single-unit and global-duplicate analytic controls, and the outside-clue
shortcut at 100% with its exclusion from the agent's sensory input. No complete-board
solve rate applies: each judgment concerns a target in a board with twelve
blanks. The counterbalanced conditions reuse saved learning histories, rather
than independently retraining earlier steps.

Require exact equality of the 16 KC input mappings and all recall spike hashes,
traces, rates, actions and memory states with the corresponding Step 3 records.
There are 528 physical evaluations per split: 16 baseline, 256 recall and 256
full erasure. Repeated presentations are recorded aliases of these measurements.

Commit source and protocol before development. Only after all development
gates pass and results are committed, evaluate the structurally reserved
layouts using the same code and memories, with no tuning or new teaching.

```sh
.venv/bin/python constraint_transfer.py --split development --out experiments/level-04/001-frozen-transfer/development
.venv/bin/python constraint_transfer.py --split heldout --reference experiments/level-04/001-frozen-transfer/development --out experiments/level-04/001-frozen-transfer/heldout
```

These output directories must not exist before a run. Use new paths to repeat
the experiment. Passing would establish assisted constraint coverage with
existing memories, not newly learned spatial rules or neural generalization.
