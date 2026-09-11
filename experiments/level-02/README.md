# Step 2: symbol comparison

Step 1's assisted visual cue-learning gate was completed in
[`level-01/005-image-adapter`](../level-01/005-image-adapter/README.md), commit
`530c0be`, before any Step 2 neural experiment began.

The comparison task uses four familiar symbols. Training presents one row
symbol plus a candidate; evaluation presents two distinct row symbols plus a
candidate. All 16 atomic pairs are trained, while all 24 unordered two-row
compositions (48 ordered rows/candidates) are withheld from reinforcement.
The environment asks whether the candidate repeats a row symbol. Both output
assignments are trained separately from baseline.

| Experiment | Status | Evidence |
| --- | --- | --- |
| [001: centered random features](001-centered-features/README.md) | Failed; stopped after the first completed paired condition |31.25%,132/192 timeouts; zero-deadband diagnostic only76.04%; near-saturated shared synapses. Commit3dfebbf. |
| [002: template routing](002-template-pilot/README.md) | Untrained calibration only | Fixed image parsing; between-group output variation motivated anatomy-only balancing. Commit30d0c7f. |
| [003: balanced templates](003-balanced-templates/README.md) | Completed development pilot; comparison gate failed | Atomic recall100% both mappings; novel compositions79.17%/100%. Commit9db2804. |
| [004: bidirectional timing](004-bidirectional-pilot/README.md) | Completed accuracy pilot; controls pending |100% both mappings with the same local rule, using both cue-before-dopamine and dopamine-before-cue teaching. |

Adequate Step 2 performance requires every mapping under both training orders
to achieve at least90% balanced accuracy, at least85% per class/candidate/view,
and at least25 percentage points above frozen, absent-feedback, and inconsistent
teaching controls. Erasure must restore baseline spike counts exactly, and no
nonplastic weights may change. Pilot modes lack the full controls and cannot
pass this gate.

Template recognition and fixed sensory pooling are explicitly engineered.
Only pair valence is learned in the existing fly synapses. Repeated image views
and row reversals are not independent generalization examples when they yield
identical neural inputs. This milestone does not establish natural fly vision,
novel-symbol equality, learned row-order invariance, or Sudoku solving.
