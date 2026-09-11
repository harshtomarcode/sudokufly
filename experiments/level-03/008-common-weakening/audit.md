# Independent audit of two-round common weakening

**The complete Step 3 gate fails.** Both mapping-0 conditions pass; both
mapping-1 conditions retain many invalid-candidate timeouts. Completion alone
would conceal this failure. No neural simulations were run for this audit.

Reviewed executed source `28b392e`, final development records, all 16 calibrated
snapshots, each original Step 2 arm's own source snapshot, and graph edge
identities. Recomputed every class/candidate/blank/view metric, score, margin,
completion result, control gap, and gate independently of the runner's metric
functions. No discrepancy was found.

| Source seed | Mapping | Paired balanced accuracy | Accept / reject recall | Paired completion | Calibrated original frozen / no-feedback / inconsistent balanced accuracy | Gate |
|---|---:|---:|---:|---:|---:|---|
| 20260919 | 0 | 100% | 100% / 100% | 100% | 16.67% / 16.67% / 4.17% | Pass |
| 20260919 | 1 | 54.17% | 100% / 8.33% | 100% | 25% / 25% / 12.50% | Fail |
| 20260920 | 0 | 100% | 100% / 100% | 100% | 16.67% / 16.67% / 4.17% | Pass |
| 20260920 | 1 | 54.17% | 100% / 8.33% | 100% | 25% / 25% / 12.50% | Fail |

All paired agents have 100% acceptance precision. Mapping 0 has 100% raw
accuracy and subgroup metrics, with minimum margin +0.125 Hz beyond the fixed
deadband. Mapping 1 has only 31.25% raw accuracy, 11/16 neural decisions time
out, the worst candidate subgroup has 50% balanced accuracy, and minimum margin
is -0.625 Hz. Both increasing and decreasing first-accept scans complete every
paired board, because the correct candidate is accepted and the other errors
are timeouts. Timeouts remain incorrect judgments.

## Identical calibration and unchanged evaluation

All 16 source-arm/mapping/order combinations receive exactly 32 calibration
events: two rounds through the same 16 groups, with the same eight preset KC
IDs per group. The schedule has no board, target, or correctness field and does
not branch on the recorded neural action. For every event, actual activity is
56 KC spikes during the frozen 500 ms cue, then zero KC spikes and 270 PAM11
plus 36 PPL101 spikes during 200 ms simultaneous DAN stimulation, followed by
250 ms with zero KC/DAN activity. The learning/frozen flags and every phase's
memory continuity match the declared schedule. All 512 events and 1,536 phases
were checked. Formerly frozen and no-feedback source arms receive the same
plastic calibration as every other arm; those names describe their Step 2
history, not the presence of dopamine during this experiment.

The development domain remains 96 grids, all 16 blank positions, four
candidates, and three views: 18,432 candidate judgments (4,608 accepts and
13,824 rejects) and 4,608 rendered boards. These alias 16 neural representations,
each occurring 1,152 times. Labels agree with the missing digit, and input
hashes reproduce the sorted graph indices. No held-out boards were evaluated.

There are 1,040 actual frozen evaluation records: 16 untrained baseline and
256 each for own-source inherited state, calibrated recall, stage erasure,
and full erasure. The four paired endpoints supply 64 physical decisions;
rendered aliases are not independent neural tests. All 500 ms trace sums
reproduce the logged MBON rates, `MBON11 - MBON07 - 1.625 Hz` score, and +/-2 Hz
decision. Each evaluation has 24 simultaneous stimulated KCs, 168 total KC
spikes from those cells, zero DAN spikes, and unchanged W/u/w. The numerical
performance, subgroup, precision, completion, and 25-point control gates remain
the same as before.

## Restoration, controls, and changes

Each calibrated arm starts from its own original Step 2 W/u/w. All snapshot
hashes and memory statistics agree with the raw records. Calibrated original
frozen and no-feedback endpoints are byte-identical across both mappings and
source orders; their calibration phases and all raw evaluation spike hashes,
traces, rates, and memory states also match exactly. Their classification
accuracy differs by mapping because the action interpretation reverses.

All 256 stage-erasure comparisons restore that arm's own original source W/u/w,
full spike hash, trace, rates, and action exactly. All 256 full-erasure
comparisons reproduce the untrained baseline. The plastic indices reproduce
exactly the original 7,835 anatomical KC-to-MBON07/11 edges. Preservation of
nonplastic edges additionally relies on the runner's whole-weight hash
assertion after resetting only plastic memory; a full post-training network
weight snapshot is not available for independent comparison.

Every one of the 452 directly stimulated plastic edges is weakened relative
to the analytic passive-decay endpoint. All unstimulated u/w values match that
passive prediction within 2e-12 over 14.4 seconds of unfrozen time. Calibrated
paired/inconsistent arms each report 909 weights changed from their inherited
state, including 457 previously learned but unstimulated edges that merely
decay. Original frozen/no-feedback arms change 452 edges from their zero-memory
baseline. Thus calibration introduces real, label-blind weakening while the
prior source associations remain the experimental distinction.

No latent or effective clipping appears at any logged calibration phase
endpoint. Final paired efficacy ranges are approximately 0.136000–1.822826,
0.135119–1.822826, 0.136069–1.823292, and 0.135655–1.823292. None is below 0.11
or above 1.99. Phase endpoints alone cannot rule out unrecorded within-phase
clipping.

For mapping 1, all twelve invalid inputs retain MBON11 rates of 14 Hz, while
eleven have MBON07 rates of 10.5–11 Hz and scores +1.875 or +1.375 Hz, below
the +2 Hz threshold. These data support a remaining spike-count threshold
problem; they do not support cancellation through reduced MBON11 activity.
Testing a third fixed calibration round is a new development dose, not a
result established by the present assay.

This experiment asks whether prior learned associations transfer after
identical calibration; it does not test added board-labelled learning.
The template parser, target-row selection, and pooling remain engineered,
and development design was informed by earlier labelled results. The reserved
structural family aliases the same 16 neural inputs. Preserve this failure
and avoid claims of a general Sudoku algorithm or novel neural generalization.
