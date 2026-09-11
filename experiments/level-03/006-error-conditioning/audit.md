# Independent audit of error-contingent conditioning

**The Step 3 gate fails.** One of four source-order/mapping conditions converges;
the other three finish below their inherited balanced accuracy. The records show
real internal synaptic learning and interference, not absent updates or a memory
restoration error. No neural simulations were run for this audit.

Reviewed the executed `one_blank.py` at `dea4bb6`, the final development raw logs,
all 16 final snapshots, the inherited Step 2 snapshots, graph edge identities,
and the predeclared protocol. Recomputed scores independently rather than using
the runner's metric functions.

| Source seed | Mapping | Paired balanced accuracy | Accept / reject recall | Completion | Frozen / no-feedback / inconsistent balanced accuracy | Gate |
|---|---:|---:|---:|---:|---:|---|
| 20260919 | 0 | 100% | 100% / 100% | 100% | 62.50% / 62.50% / 50% | Pass |
| 20260919 | 1 | 33.33% | 50% / 16.67% | 50% | 50% / 50% / 37.50% | Fail |
| 20260920 | 0 | 54.17% | 50% / 58.33% | 50% | 62.50% / 62.50% / 45.83% | Fail |
| 20260920 | 1 | 33.33% | 50% / 16.67% | 50% | 50% / 50% / 37.50% | Fail |

All paired arms have 100% acceptance precision: their remaining errors are
timeouts, not false acceptances. That does not make the judgments correct.
Paired raw accuracies are 100%, 25%, 56.25%, and 25%. The minimum target margins
beyond the unchanged 2 Hz deadband are +0.375, -2.375, -1.875, and -1.875 Hz.
Every candidate, blank position, view, and class metric, plus every 25-point
control comparison, was recomputed and agrees with the saved gate. The three
failed conditions each have a candidate subgroup at 0% balanced accuracy.

## Coverage and accounting

The development manifest contains 96 grids, all 16 blank positions, all four
candidates, and three rendered views: 18,432 judgments, with 4,608 accepts and
13,824 rejects. Labels agree with the missing digit in the saved complete grid.
The manifest covers 4,608 rendered boards (1,536 distinct masked grids across
three views). All presentations use development grids; the held-out structural
family was not evaluated.

These images collapse to **16 neural inputs**, each aliased by 1,152 development
presentations. Each input has one consistent label and exactly 24 existing KC
IDs; reconstructing sorted graph indices reproduces its input hash. They are
the same 16 representations used in conditioning. There are 848 physical frozen
evaluation records: 16 untrained baseline, 64 inherited-state, 256 final recall,
256 stage-erasure, and 256 full-erasure measurements. The four paired endpoints
therefore contribute 64 physical decisions, not 73,728 independent neural tests.

The 500 ms trace sums reproduce all logged MBON rates and the fixed
`MBON11 - MBON07 - 1.625 Hz` score. Thresholding at +/-2 Hz and reversing semantic
actions only for mapping 1 reproduces every action. All evaluation memory
before/after records agree; all evaluation DAN counts are zero. Each evaluation
records 168 total KC spikes, all from the 24 stimulated cells.

First-accept selection scans candidates 1 through 4 without grading feedback.
Independently comparing its selected digit with the unique completion reproduces
the completion statistics; reversing the scan gives the same results here.
Frozen and no-feedback controls still complete 100% of boards despite only
62.5% or 50% balanced judgment accuracy, demonstrating why completion alone
cannot establish candidate rejection.

## Teaching and causal controls

Audited all 3,072 frozen pre-feedback training judgments and 6,320 subsequent
phase records. Each arm has eight fixed 24-trial epochs; every accept input
appears three times and every reject input once per epoch. The independently
reconstructed seeded cue order matches exactly. Every paired teaching event is
triggered by an incorrect or undecided raw action, and its target pulse agrees
with the label/mapping. Correct trials remain frozen. Every phase's memory
continues from the preceding phase/trial without an unintended reset.

Paired teaching-event counts are 13, 129, 60, and 114. Frozen/no-feedback replay
the exact paired event schedule. Inconsistent arms reproduce the declared
shuffle of all events, including no-teaching entries, and preserve total event
and target-orientation counts. Their active teaching contradicts the input's
target on 8/13, 63/129, 33/60, and 66/114 events. This is a control with relocated
teaching windows, not matched active windows or per-input balanced feedback.

Each event in paired, frozen, and inconsistent arms has 270 PAM11 and 36 PPL101
spikes, with the logged before/after ordering selecting the learning sign.
No-feedback has zero DAN spikes. The pinned local rule contains the negative
current-DAN times retained-KC-trace term after the cue, and the positive current-KC
times retained-DAN-trace term after the opposite pulse. All frozen phases preserve
effective and latent memory. Training's `selected_KC_spikes = 0` when no KC list
is supplied is a logging convention; it does **not** establish absence of all
unstimulated KC firing during those phases.

All arms restore the same paired Step 2 W/u/w within each condition. Frozen
snapshots remain byte-identical to that inherited state. No-feedback changes are
expected passive relaxation: its final u/w agrees within 2e-12 with the analytic
two-state decay solution for 1.2 seconds of unfrozen time per teaching event.
Each unfrozen endpoint differs from inherited memory on 909 edges, but this
number includes drift. Compared with its matched no-feedback snapshot, paired
associative differences occupy only 308, 452, 338, and 452 directly stimulated
edges; inconsistent differences occupy 425, 452, 452, and 452. All 457 inherited
but unstimulated edges agree exactly with no-feedback in W/u/w. No other plastic
edges acquire additional changes.

Snapshot indices reproduce exactly the original 7,835 anatomical KC-to-MBON07/11
edges. Snapshot hashes and all reported memory statistics reproduce the records.
All 256 stage-erasure comparisons restore inherited W/u/w, scores, full spike
hashes, and traces exactly; all 256 full-erasure comparisons restore the untrained
baseline. Nonplastic preservation is supported by static inspection and the
runner's full-weight hash assertion after reset; no full-network post-training
weight snapshot is independently available.

## Learning failure and clipping

| Seed / mapping | Teaching events | Latent lower-clamp phase endpoints | Effective lower-bound phase endpoints | Largest simultaneous effective lower-bound count |
|---|---:|---:|---:|---:|
| 20260919 / 0 | 13 | 4 | 2 | 12 |
| 20260919 / 1 | 129 | 71 | 67 | 16 |
| 20260920 / 0 | 60 | 31 | 29 | 13 |
| 20260920 / 1 | 114 | 62 | 58 | 16 |

For example, the successful condition reaches `u_min = -0.9` at trials 14, 27,
28, and 35, and 12 effective weights reach the lower bound at trials 27 and 35.
Every final paired snapshot has zero weights within the runner's strict
at-bound tolerances, but this is **not evidence that training never clipped**.
Final efficacy ranges are approximately 0.100475–1.999861, 0.101673–1.998529,
0.100475–1.999861, and 0.102870–1.997198. Counts below 0.11 / above 1.99 are
25/32, 64/48, 25/32, and 48/37. Inconsistent arms also show clipping in three
conditions. Phase endpoints cannot identify distinct clipped edges or exclude
additional clipping inside a phase, including at the upper bound.

The successful condition has 8 then 5 errors in its first two epochs and none
in the final six. The other final epochs still require 21, 9, and 21 teaching
events. For seed 20260919/mapping 1, epoch errors grow from 13 to 21; its final
MBON11 rate is 14 Hz on 14/16 inputs, including two valid candidates whose
inherited negative responses were lost. Shared pair features receive conflicting
teaching, while strong matching features approach their bounds. This supports
interference and limited operating range as explanations; it does not isolate
either as the sole cause. Depression-only conditioning is a separate mechanistic
test, not an outcome established by this assay.

The fixed template vision, target-row selection, and pooling remain engineered.
Only internal fly-edge valence changes are learned. These development results
do not demonstrate a general Sudoku algorithm, learned visual invariance, or
generalization to unseen neural representations. Step 3 remains incomplete.
