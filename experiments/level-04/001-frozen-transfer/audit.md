# Independent Step 4 audit

This review independently checked dataset construction, geometric symmetries,
pixel routing and scoring for the frozen source at `0bd3d45`. The reviewer ran
data-only calculations and image encoding; no additional neural simulation or
training was performed. Development artifacts have passed the independent
checks below. Reserved-layout confirmation remains pending.

## Dataset and independence of the split

Independent enumeration reproduced all 288 valid complete 4×4 grids. For each
highlighted empty target, the construction includes two possible row-only
positions, two column-only positions, the single diagonal box-only position,
and eight positions outside every target unit. Thus there are
`16 × 2 × 2 × 1 × 8 = 512` target/occupied-position layouts.

Row-only positions are outside the target box; column-only positions are also
outside that box. The box-only position differs from the target in both row
and column. Each occupied location consequently isolates exactly its declared
constraint. All four clue values differ, so the initial givens have no direct
rule violations. This alone does not ensure a completion.

An independent canonicalization over the 128 allowed geometric Sudoku maps,
using only target and occupied positions, reproduced these five orbits:

| Target and occupied-position key | Layouts | Completions per assignment | Split |
| --- | ---: | ---: | --- |
| `(0,2,5,6,8)` | 128 | 2 | Development |
| `(0,2,5,7,8)` | 128 | 1 | Development |
| `(0,2,5,8,10)` | 64 | 0 | Excluded |
| `(0,2,5,8,11)` | 128 | 1 | Held out |
| `(0,2,5,8,15)` | 64 | 1 | Held out |

Completion counts were checked against the independently enumerated full
solution universe. The other 23 distinct-digit assignments are global digit
relabelings, which preserve these counts. Excluding the uncompletable orbit
therefore leaves 448 eligible layouts. This filter occurs in dataset creation,
not in the sensory encoder or action selection.

The split also respects the underlying unhighlighted board. Independent
canonicalization of occupied masks **without the target** gives development
keys `(0,1,8,14)` and `(0,2,5,11)`; held-out keys `(0,2,9,15)` and
`(0,6,9,15)`; and excluded key `(0,2,8,15)`. No occupied-mask geometry orbit,
exact occupied mask, or underlying digit-assigned board crosses the split.
All digit relabelings, candidate choices and rendered views remain together.

| Quantity | Development | Held out | Combined |
| --- | ---: | ---: | ---: |
| Target/occupied layouts | 256 | 192 | 448 |
| Distinct unhighlighted occupied masks | 256 | 80 | 336 |
| Distinct underlying partial grids | 6,144 | 1,920 | 8,064 |
| Highlighted board–target cases | 6,144 | 4,608 | 10,752 |
| Candidate judgments before views | 24,576 | 18,432 | 43,008 |
| Presentations across three views | 73,728 | 55,296 | 129,024 |
| Presentations per outcome kind | 18,432 | 13,824 | 32,256 |

Some held-out partial grids support multiple highlighted targets. The 10,752
count therefore describes marked board–target cases, not unique underlying
partial grids. Each split covers every target equally and every candidate
equally. The four kinds—legal, row, column and box—are equally frequent;
binary accept/reject labels have the declared 1:3 imbalance.

## Grader, matched examples and score checks

The grader directly inspects the target's row, column and 2×2 box. It does not
consult a solution, the neural input, or the saved memory. It rejects multiple
simultaneous conflicts, which cannot occur in this declared construction.
Each legal case has the candidate digit at the outside location. Swapping
that digit with the row-only, column-only or box-only clue preserves the
highlighted target, occupied cells, candidate identity and complete clue-digit
histogram while producing the corresponding isolated violation.

Data-only enumeration checked all presentations and all matched swap lookups.
There are 18,432 legal/reject pairs per constraint in development and 13,824
per constraint in confirmation, counting all three views. Scoring requires
both explicit actions to be correct; a timeout cannot satisfy either member.
Perfect supplied actions yield 100% balanced accuracy and matched-pair
success. Always-reject actions yield 50% balanced accuracy and zero matched
pair success. A row-only supplied policy yields 66.7% balanced accuracy,
100% row pair success and zero column/box pair success. Column-only and
box-only policies have the same overall balanced accuracy by construction;
any policy checking only two constraints reaches at most 83.3% in this
restricted family when it otherwise accepts.

The dataset permits a perfect **outside-clue identity shortcut**: since the
four clues differ, selecting the outside clue's value identifies every legal
candidate. This is a limitation of the assay, not evidence of a learned rule.
The implemented encoder does not route the outside clue. A global duplicate
detector, in contrast, sees the candidate once on every board and obtains
only 50% balanced accuracy by rejecting everything.

An additional 240 pixel-level counterfactuals changed the outside clue to
each digit or removed it, while retaining the target, candidate and attended
clues. All neural input arrays remained exactly unchanged. These checks
include every candidate, view and eligible orbit representative; they verify
the exclusion of this shortcut from the supplied sensory input.

## Pixel routing and limits of the neural claim

The encoder receives only rendered pixels. It detects exactly one highlighted
empty target by the declared color cue, considers the union of its seven
unique peer locations, ignores empty interiors and routes the three occupied
peers through the saved independently permuted template banks. The fixed
Cartesian candidate/peer code supplies no equality or legality branch. Each
of the three distinct codes selects eight existing KCs, giving 24 distinct
stimulated KCs independent of the label.

Data-only rendering and encoding checked 6,480 cases: every eligible layout
with a fixed distinct-digit assignment, plus all 24 digit assignments for
one representative of each eligible orbit, using every candidate and all
three views. Highlight locations, attended positions, independently mapped
template identities and pair codes were correct throughout. Every encoded
case used 24 distinct KCs, and the cases produced 16 distinct inputs.
Separately, all digit assignments and candidates from every eligible orbit
representative reproduced exactly the 16 physical KC-ID sets saved in Step 3.

Target-unit membership, symbol recognition and spatial pooling are engineered
parts of the interface. Pooling removes the row/column/box role of a clue;
the network receives the same learned comparison representations regardless
of the isolated constraint being tested. Structural board separation must
therefore not be described as novel neural input generalization. This assay
tests frozen transfer of prior synaptic histories. It does not train spatial
rules, demonstrate the need for new Step 4 feedback, support arbitrary clue
occupancy or solve sequential multi-blank Sudoku puzzles.

## Development runtime verification

The completed development run passed all four saved-memory conditions in
155.9124 seconds. Independently verified all 19 artifact hashes, all four
source hashes against both the working files and frozen commit `0bd3d45`,
and every referenced source-memory snapshot hash. The protocol records zero
training epochs and the summary records no new learning.

An independent immediate-rule implementation regraded all 73,728 saved
presentations and matched every stored label and isolated-conflict kind. All
presentation keys were unique within the declared layout/digits/candidate/view
domain. Recomputed balanced accuracies, per-kind recalls and every matched
pair result directly from neural actions; they agree with the summaries.

| Source order | Mapping | Paired balanced accuracy | Frozen | No feedback | Inconsistent | Minimum paired margin |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 20260919 | 0 | 100% | 0% | 0% | 12.5% | +0.375 Hz |
| 20260919 | 1 | 100% | 0% | 0% | 16.67% | +0.125 Hz |
| 20260920 | 0 | 100% | 0% | 0% | 0% | +0.375 Hz |
| 20260920 | 1 | 100% | 0% | 0% | 4.17% | +0.375 Hz |

Every paired condition has 100% raw accuracy, both binary class recalls,
each isolated-constraint recall, precision, candidate/target/view balanced
accuracy and matched-pair success, with no timeouts. All predeclared numeric
gates pass. The unchanged initial-memory baseline times out, so its observed
accuracy is 0%; this is distinct from the analytic always-reject policy.

The run contains exactly 528 physical neural evaluations: 16 baseline, 256
recall and 256 full-erasure evaluations. All 16 saved KC input mappings are
exactly equal to Step 3, including their input hashes and ordered physical
neuron IDs. Every one of the 256 recall records equals its corresponding
Step 3 record in full-network spike hash, output rates, decision score,
action, total and selected KC spike counts, DAN spike counts, complete trace
and effective/latent memory states. Every erased response equals its
corresponding baseline response in those fields. Before/after memory states
are identical throughout all 528 evaluations; no DAN spikes occurred.

The source also restores the original full weight state before each snapshot
and verifies its hash after full erasure. Nonplastic preservation is supported
by this execution path and frozen update semantics; no separate full-weight
snapshot immediately after recall is retained for a further independent
array comparison.

These results reproduce the existing 16-input behavior under a new assisted
spatial interface. The narrowest +0.125 Hz margin is inherited from Step 3;
the deterministic checks do not establish perturbation or physiological
robustness. Repeated board/view aliases and the two answer mappings do not
constitute additional independent training replicates.

## Reserved-layout confirmation

Pending the frozen confirmation run and independent artifact checks.
