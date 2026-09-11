# Independent audit of depression-only conditioning

**All paired agents reach 100% performance, but all four conditions fail the
predeclared added-learning gate.** Shuffled feedback also improves performance,
leaving less than the required 25 percentage-point advantage. These are real
synaptic changes and successful responses; the stronger causal claim remains
unestablished. No neural simulations were run for this audit.

Reviewed source `629766e`, its changes from `dea4bb6`, the final protocol,
all raw development records, all 16 endpoint snapshots, original graph edge
identities, and the saved Step 2 source memories. Independently reconstructed
metrics, cue/event schedules, memory statistics, and erasure comparisons.

| Source seed | Mapping | Paired balanced accuracy | Inconsistent balanced accuracy | Gap | Teaching events | Last teaching trial, zero-based | Minimum margin beyond deadband |
|---|---:|---:|---:|---:|---:|---:|---:|
| 20260919 | 0 | 100% | 87.50% | 12.50 points | 5 | 23 | +0.375 Hz |
| 20260919 | 1 | 100% | 83.33% | 16.67 points | 18 | 44 | +0.125 Hz |
| 20260920 | 0 | 100% | 91.67% | 8.33 points | 5 | 12 | +0.375 Hz |
| 20260920 | 1 | 100% | 87.50% | 12.50 points | 17 | 40 | +0.375 Hz |

Each paired endpoint also has 100% raw accuracy, class recall, acceptance
precision, candidate/blank/view metrics, and board completion, with no timeouts.
Both increasing and decreasing candidate scans complete every board. Frozen
and no-feedback balanced accuracies remain 62.5% for mapping 0 and 50% for
mapping 1; both still complete every board despite their incorrect timeout
judgments. Inconsistent arms retain all correct accepts but time out on some
rejects. Thus performance gates pass for paired agents, and the inconsistent
control comparison alone makes each condition fail. The saved overall failure
is correct; held-out boards were not evaluated.

## Unchanged interface and evaluation

Grid, input, and presentation manifests are byte-identical to experiment 006.
They contain 96 development grids, every blank position and candidate, and
three views: 18,432 judgments, comprising 4,608 accepts and 13,824 rejects.
The 4,608 rendered boards represent 1,536 distinct masked grids across three
views. All labels agree with the unique missing digit. The images collapse
to the same 16 trained neural inputs, each represented by 1,152 presentations.

Verified unchanged source parameters, eight epochs, 24 simultaneous KCs,
current 30, output current 5.5, offset 1.625 Hz, and +/-2 Hz deadband.
Source hashes match the executed files. All 848 physical frozen evaluations
were checked: 16 baseline, 64 inherited, 256 final recall, 256 stage-erasure,
and 256 full-erasure. The four paired endpoints contain 64 actual decisions,
with rendered records aliasing those responses. No results are reused across
memory states or arms.

Trace sums reproduce every logged output rate, score, and action. All onset
times are zero. Each inference records 168 total KC spikes, all from the
24 selected KCs, zero DAN spikes, and identical effective/latent memory before
and after. Every class/subgroup metric, first-accept selection, margin, and
control-gap calculation agrees with an independent recomputation.

## Teaching, control integrity, and memory

Checked all 3,072 pre-feedback judgments and 360 additional training phases.
There are 192 trials per condition/arm: each epoch presents four accept inputs
three times each and twelve reject inputs once each. Independently regenerated
cue permutations match. Every paired pulse follows a wrong or undecided action
and has the correct mapped target. Correct trials preserve memory. All paired
errors here are invalid-candidate timeouts, so only the rejection-associated
DAN compartment receives teaching within each mapping.

Each teaching event has exactly two phases: target DAN for 200 ms with learning,
then 250 ms passive relaxation. Whole-KC logging confirms zero KC spikes during
both phases; the retained cue trace supplies the negative local update.
Actual DAN spikes are 36 PPL101 for an aversive pulse or 270 PAM11 for a reward
pulse, with zero activity in the other compartment. No-feedback DAN counts are
zero. Frozen phases preserve W/u/w. Phase and trial memory continuity checks pass.

Frozen/no-feedback arms replay each paired event exactly. Inconsistent schedules
match the declared permutation of all events, including no-teaching entries.
Event totals and target-pulse counts are preserved; active windows move. The
inconsistent schedules contradict the input's target on 4/5, 7/18, 3/5, and
11/17 teaching events. Their improvement therefore cannot be dismissed as an
accidentally correct shuffled schedule. This is not a per-input balanced or
active-window-matched control.

Every arm starts from the same paired Step 2 W/u/w within its condition.
Frozen endpoints equal that source exactly. No-feedback u/w agrees within
2e-12 with analytic passive relaxation for 0.45 seconds per teaching event.
Relative to no-feedback, paired snapshots change 132, 256, 135, and 256 existing
stimulated edges; inconsistent snapshots change 123, 256, 133, and 240. All
these additional u/w changes are negative. All other plastic-edge W/u/w entries
match no-feedback exactly. The larger count of 909 edges changed from inherited
memory includes passive decay and must not be called 909 newly learned edges.

The plastic indices reproduce exactly the original 7,835 anatomical KC-to-
MBON07/11 edges. Snapshot hashes and memory statistics agree with the logs.
All 256 stage-erasure comparisons reproduce inherited W/u/w, full spike hashes,
rates, scores, actions, and traces; all 256 full-erasure comparisons reproduce
the original baseline. Nonplastic preservation additionally relies on the
runner's full-weight hash assertion after resetting only plastic memory;
there is no independently saved full-network post-training weight snapshot.

## Bounds and interpretation

Mapping 0 shows no clipping at logged phase endpoints. Mapping 1 reaches the
latent lower clamp at 10 and 9 endpoints, and effective lower bounds at 6 and
5 endpoints; up to 16 effective weights are simultaneously at the lower bound.
Both final mapping-1 snapshots have 64 weights below 0.11 efficacy, with minimum
0.10010016. Their final strict at-bound counts are zero, which does not erase
the observed transient clipping. Final efficacy ranges are approximately
0.131864–1.828943, 0.100100–1.826253, 0.131430–1.828868, and 0.100100–1.826385.
Inconsistent mapping-1 arms also show latent clipping. Endpoint logs cannot
exclude additional within-phase clipping.

All paired agents stop making errors within two epochs and remain correct
through the remaining fixed schedule. Compared with 006, removing the second
sequence also changes dopamine dose, cue exposure, and elapsed learning time;
it is a teaching-schedule comparison, not an isolated sign intervention.
The results are consistent with existing Step 2 associations becoming usable
after common weakening of shared inputs. Because mostly contradictory feedback
also helps, they do not establish that correct new input-feedback associations
were necessary for that improvement.

Template vision, target-row selection, and pooling remain engineered. This is
an all-candidate, one-blank 4x4 task using previously learned internal fly-edge
memory, not a general Sudoku algorithm. The reserved board family aliases the
same 16 neural inputs. Preserve the failed incremental-learning gate and do
not claim novel neural generalization or new board-specific knowledge.
