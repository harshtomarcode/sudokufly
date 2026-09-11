# Independent scientific and raw-results audit

Audited 2026-09-10 against executed source commit `5aa3db1` and the completed
experiment 005 records. This audit recomputed results from raw records and
examined saved memory arrays, graph indices, annotations, and the pinned
learning rule. It did not rerun neural simulations. Artifact and provenance
verification is reported separately.

**All four mapping/order conditions pass the declared Step 2 gate.** The
supported result is learned comparison of four familiar symbols on new two-cell
compositions, through the declared engineered parser and sensory interface.

## Behavioral gate and sample accounting

| Training order | Mapping | Paired accuracy | Frozen / no feedback / inconsistent | Minimum paired margin |
|---|---|---:|---:|---:|
| 20260919 | 0 | 100% | 8.33% / 8.33% / 8.33% | 3.125 Hz |
| 20260919 | 1 | 100% | 0% / 0% / 0% | 3.125 Hz |
| 20260920 | 0 | 100% | 8.33% / 8.33% / 8.33% | 3.125 Hz |
| 20260920 | 1 | 100% | 0% / 0% / 0% | 3.125 Hz |

Targets, thresholded actions, correctness, balanced accuracy, every candidate,
both classes, every view, and each match position were independently recomputed.
Every paired subgroup scores 100%; all margins are measured beyond the fixed
2 Hz deadband. Each run exceeds each control by at least 91.67 percentage
points. All 16 trained atomic images are also recalled correctly in each paired
state. Each control has 22 timeouts among 24 measured test inputs; these low
accuracy values must not be described as ordinary binary chance performance.

Each trained state is evaluated on **24 distinct neural test inputs**, covering
48 ordered cases in four renderings. Each input has eight records: one measured
and seven aliases. Across the four paired states this gives **96 actual test
decisions and 672 aliases**, representing 768 case/view records. It is the same
24-case unordered domain across states, not 96 different tasks.

The complete log has 8,704 top-level records: 1,536 training trials and 7,168
evaluation records. The latter comprise **1,120 actual frozen evaluations and
6,048 aliases**, including baselines, training-image recall, controls, and
erasure. Every alias points to the first actual measurement of its exact KC
input within the same evaluation call. All groups are equally sized, so alias
weighting does not alter the reported aggregate accuracy. No response is reused
across memory states, arms, mappings, or erasure.

## Teaching and controls

All 1,536 training trials and their six recorded phases were checked. Each cue
phase produces 112 spikes exclusively in the selected 16 KCs, with zero DAN
spikes. Imposed DAN phases have zero KC spikes and exactly the indicated
population response: 270 reward-cell spikes or 36 aversive-cell spikes. Both
consolidation phases have zero KC and DAN spikes.

These observations support the intended signs under the exact upstream rule:
cue followed by DAN has the negative term with a positive KC trace; DAN followed
by cue has the positive term with a positive DAN trace. Frozen pre-cue DAN
stimulation updates traces while preserving memory. The intermediate reset
clears electrical state and traces while retaining effective weights and `u/w`.

Frozen controls receive identical pulse schedules and freeze all six phases.
No-feedback controls omit both pulses while keeping the same phase durations.
For every image, inconsistent timing is exactly balanced between the two
assignments: six of each for matching pairs and two of each for nonmatching
pairs. Each reinforced trial supplies one pulse to each compartment, with
valence selecting their temporal placement. This is supervised associative
teaching, not reinforcement contingent on an action.

## Stored mechanism, bounds, and recovery

All 16 snapshots use exactly the original 7,835 eligible edge indices and were
compared with the earlier untrained frozen snapshot. Graph source/target indices
and neuron annotations identify **909 existing edges from the 256 sensory KCs
to MBON07/11**. These are the only edges with changed effective or latent memory
in the paired and inconsistent arms; all other eligible edges remain unchanged.

In mapping 0, paired training strengthens 427 and weakens 482 edges. Mapping 1
reverses those counts and the sign of every affected edge. Every sign agrees
with the assigned cue valence and target compartment: an accept association
weakens MBON07 inputs and strengthens MBON11 inputs; reject does the reverse.
Snapshot effective-weight and `u/w` hashes agree with recorded summaries and
frozen evaluation states.

Across paired runs, effective and latent efficacy fractions remain approximately
**0.25607–1.82998**. No value reaches, or comes within 0.01 of, either model bound
at 0.1 or 2.0. Inconsistent teaching also changes all 909 edges, but produces
only weak potentiation, at most approximately 1.05413 of baseline. It is a
control for consistent association, not a no-plasticity control.

Frozen and no-feedback arms retain exactly the untrained weights and zero
latent deviations throughout every recorded phase. Their test spike hashes
match baseline. Every erased evaluation restores baseline effective/latent
memory summaries and full spike-count hashes: **384 independently simulated
erasure comparisons**, represented by 3,072 case/view records. All frozen
evaluation before/after memory summaries agree.

The runner additionally checks unchanged nonplastic connections with a
full-network weight hash after temporarily restoring the plastic subset to
baseline. The assertion implementation and all completed outcomes were
inspected. Plastic-only snapshots cannot independently reconstruct historical
nonplastic arrays; the full-network preservation conclusion relies on that
runtime invariant. The snapshot audit independently establishes the absence
of added plastic indices and confines all stored changes to the expected
existing sensory connections.

## Artifact provenance and milestone prerequisites

A separate independent artifact audit verified all **71 listed file hashes**:
27 in the probe and 44 in training, with exact directory inventories including
both summaries. The source hash matches executed commit `5aa3db1`; the imported
source, original graph-weight hash, and probe reference also match. All 16
snapshots satisfy `W = W_initial * (1 + w)` within their recorded float format.
The working source subsequently changed only two explanatory docstrings; an
AST comparison with docstrings removed confirms identical execution. Replaying
the archived reference requires `5aa3db1`; current code requires a fresh probe.

The fixed routing seed changes 15 of 16 atomic neural inputs and every two-row
input from the development pilot. All 208 image/code manifest records were
reconstructed: 16 distinct training codes, 24 distinct test codes, no conflicting
labels and no training/test code overlap. Anatomy, template construction, and
pair allocation were reproduced without labels. Both fresh orders contain 96
trials with 48/48 class exposure. No settings were tuned on this replication.

The preceding assisted visual Step 1 was completed and committed in `530c0be`
before Step 2 began. Step 2 development failures, untrained calibrations, pilots,
and the pre-training frozen replication are separately retained in Git. Root
verification additionally checked all 299 recorded artifact hashes across the
Step 2 experiment history, Python syntax, and the final whitespace diff.

## Scope

This is four separately trained states in one connectome, using one fresh
template-to-neuron routing seed and two fresh training orders. The protocol was
developed on the same small task domain, then frozen for this replication; it is
not an untouched task-distribution evaluation.

Template recognition, row-order invariance, selection of eight representatives
per constituent pair, and input pooling are engineered. All atomic pairs are
familiar; their two-cell compositions are absent from training. Performance
therefore supports internal valence learning that transfers through this fixed
compositional interface. It does not establish learned natural fly vision,
abstract equality for unseen symbols, a learned search or pooling algorithm,
Sudoku solving, or an advantage over simpler associative models.
