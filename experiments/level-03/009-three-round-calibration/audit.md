# Independent audit of three-round common weakening

**All four conditions fail the unchanged Step 3 gate.** A third calibration
round loses two mapping-0 rejections and gains only one mapping-1 rejection.
Both mappings still complete every board because their errors are timeouts
rather than false acceptances. No neural simulations were run for this audit.

Reviewed executed source `28b392e`, the predeclared three-round protocol,
all development records and endpoint snapshots, original Step 2 source
memories, and anatomical edge identities. Independently recomputed decoding,
all metrics and control gaps, calibration schedules, memory statistics, and
both erasure comparisons. No implementation or raw-accounting discrepancy
was found.

| Source seed | Mapping | Paired balanced accuracy | Accept / reject recall | Raw accuracy | Calibrated original frozen / no-feedback / inconsistent balanced accuracy | Gate |
|---|---:|---:|---:|---:|---:|---|
| 20260919 | 0 | 91.67% | 100% / 83.33% | 87.50% | 20.83% / 20.83% / 20.83% | Fail |
| 20260919 | 1 | 58.33% | 100% / 16.67% | 37.50% | 25% / 25% / 25% | Fail |
| 20260920 | 0 | 91.67% | 100% / 83.33% | 87.50% | 20.83% / 20.83% / 20.83% | Fail |
| 20260920 | 1 | 58.33% | 100% / 16.67% | 37.50% | 25% / 25% / 25% | Fail |

Paired precision and first-accept completion are 100% in all conditions, under
both increasing and decreasing candidate order. Mapping 0 has two timeouts
among sixteen inputs, a worst candidate balanced accuracy of 66.67%, and
minimum target margin -0.375 Hz beyond the fixed deadband. Mapping 1 has ten
timeouts, a worst candidate score of 50%, and minimum margin -0.625 Hz. All
class/candidate/blank/view metrics agree with independent recomputation.
Mapping 0's overall balanced score exceeds 90%, but its reject recall is below
the required 85%; it must not be reported as passing.

## Calibration and reproducibility

The only experimental change from 008 is the declared third round. For each
of all sixteen source-arm/mapping/order combinations, the first 32 calibration
records are exactly identical to 008, including every phase's full spike hash,
score, and W/u/w summary. The third round supplies the final sixteen events;
no intermediate checkpoint is selected for evaluation.

Checked all 768 calibration events and 2,304 phases. Every arm receives the
same group order and eight preset KC IDs per group, without a label, board,
mapping, or score selecting events. Every 500 ms frozen cue produces 56 total
KC spikes from the selected cells and zero DAN spikes. Each subsequent 200 ms
learning phase has zero KC spikes, 270 PAM11 spikes, and 36 PPL101 spikes.
The final 250 ms passive phase has zero KC/DAN activity. Learning flags,
durations, effective/latent memory continuity, and frozen-phase invariants
match throughout. Formerly frozen/no-feedback source arms undergo the same
plastic calibration; their names describe their earlier source histories.

## Evaluation, controls, and erasure

Coverage remains the same 96 development grids, all sixteen blank positions,
four candidates, and three views: 18,432 judgments, 4,608 rendered boards,
and sixteen neural representations. Each representation has 1,152 rendered
aliases. Labels agree with the unique missing digit, and KC index hashes
reproduce the saved inputs. No held-out boards were evaluated.

All 1,040 physical frozen evaluations were checked: sixteen original-baseline
measurements and 256 each for own-source inherited state, calibrated recall,
stage erasure, and full erasure. The four paired endpoints contain 64 actual
neural decisions, not 73,728 independent neural trials. Trace sums reproduce
every MBON rate, fixed `MBON11 - MBON07 - 1.625 Hz` score, and +/-2 Hz action.
All inference onsets are zero; each evaluation records 168 total KC spikes
from 24 stimulated KCs, zero DAN spikes, and unchanged W/u/w. No numerical
performance or control threshold changed.

Every arm starts from its own original Step 2 W/u/w. All snapshot hashes,
memory statistics, and source restoration records agree. Calibrated original
frozen and no-feedback memories, calibration phases, and every raw evaluation
spike hash/trace are identical across both mappings and source orders. Their
semantic accuracy differs only because the action interpretation reverses.

All 256 stage-erasure comparisons reproduce each arm's own inherited W/u/w,
spike hash, rate, action, and trace exactly; all 256 full-erasure comparisons
reproduce the original baseline. Plastic indices reproduce exactly the
original 7,835 anatomical KC-to-MBON07/11 edges. The 452 directly stimulated
edges all weaken beyond the passive-decay prediction; unstimulated u/w agrees
with that prediction within 2e-12 over 21.6 seconds of unfrozen time. Counts of
909 changed edges in paired/inconsistent arms include 457 inherited edges
that merely decay. Original frozen/no-feedback arms change only 452 edges.
Nonplastic preservation additionally relies on the runner's full-weight hash
assertion after resetting only plastic memory; no full post-training network
weight snapshot is independently available.

## Bounds and interpretation

Each paired condition reaches the latent lower clamp `u = -0.9` at four
logged post-DAN endpoints during the third round. No effective weight reaches
the runner's strict lower-bound tolerance at a logged endpoint, and all final
strict at-bound counts are zero. Final minimum efficacy is nevertheless
0.10054982 in every condition; 48 mapping-0 edges and 64 mapping-1 edges lie
below 0.11. Final maxima are approximately 1.81954–1.82001. Thus this assay
does exhibit latent clipping. Phase summaries cannot rule out additional
within-phase clipping.

In the first source's mapping 0, the two newly undecided inputs both propose
an invalid candidate 3. Their MBON07 rate falls to 11 Hz while MBON11 remains
11 Hz, leaving -1.625 Hz and losing the negative decision. The added weakening
therefore harms one mapping while only slightly helping the opposite mapping.
The dose change does not resolve the complete task.

This is a development-selected calibration of existing associations, not
board-labelled acquisition. The fixed template parser, target-row attention,
and pooling remain engineered. The reserved board family still aliases the
same sixteen neural representations. Preserve the failed outcome and do not
claim a learned general Sudoku rule or novel neural generalization.
