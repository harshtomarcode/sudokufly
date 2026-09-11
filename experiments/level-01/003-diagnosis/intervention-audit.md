# Independent phase and checkpoint intervention audit

Read-only audit of `diagnose_step1.py`, `phases.json`, and `snapshots.json` on
2026-09-10. No additional neural simulations were run for this audit. These are
post-hoc diagnostics of the recorded pilots, not independent learning validation.

## Reproduction and intervention correctness

- Both completed suites record source SHA-256
  `d9bfd88ad8b0ae495a28ba371017cb1f18e2bebebaea5ef6f81137f49536353a`.
  This exactly matches `git show e8df3db:diagnose_step1.py`. Their recorded Git
  HEAD is the earlier `e20b034` because the diagnostics started before the
  checkpoint commit. The subsequently added transition suite changes the current
  file hash; the committed source remains available for reproducing these suites.
- Both JSON row arrays exactly match their respective progress JSONL files.
- Phase diagnostics reproduce the first learned trial's complete observation
  spike hash and final changed-edge count for both label mappings in both pilots.
- All eight nominal checkpoint observations reproduce the complete spike hashes
  of both matching original evaluation repetitions in experiment 002: untrained,
  learned mapping 0, learned mapping 1, and shuffled mapping 1, for both cues.
- All 48 checkpoint observations freeze weights and report zero weight movement.
  Each starts with restored weights, latent memory, and fresh electrical state;
  warmup conditions deliberately add 500 ms of frozen blank exposure first.
- Selective restorations reset chosen KC-to-MBON efficacies and latent states to
  their original values. They do not remove connections. Reported restored-edge
  counts include selected connections that may already have original efficacy.

No reset, memory-restoration, or freezing implementation error was identified.
The phase and checkpoint interventions do what their recorded descriptions say.

## Phase findings

With no external reward or aversive stimulation, the horizontal cue produces:

| Measurement | 500 ms observation | 200 ms continuation | 250 ms blank settle |
| --- | ---: | ---: | ---: |
| Baseline KC spikes | 16 | 5 | 2,728 |
| Baseline active KCs | 4 | 2 | 1,391 |
| Baseline weight L1 movement | 4.171667 | 1.881582 | 531.047363 |
| Expanded KC spikes | 16 | 5 | 3,469 |
| Expanded active KCs | 4 | 2 | 1,380 |
| Expanded weight L1 movement | 19.449739 | 14.746600 | 2,430.040039 |

Final changed connections reach 2,602 baseline and 10,707 expanded without an
external teaching pulse. The corresponding vertical sequences have only eight
blank-interval KC spikes and five/60 final changed connections. The observation
phase already supplies 97 endogenous PPL spikes for horizontal versus 16 for
vertical, with zero PAM spikes for both.

Across all three horizontal pulse conditions, the blank interval contributes
98.57%-98.93% of the sum of phase endpoint L1 movements. With no external pulse,
its signed weight change is +519.644714 baseline / +2,370.234619 expanded, so
potentiation strongly dominates this interval's endpoint movement. This is
consistent with the rule's potentiating term when broad KC activity follows
earlier DAN activity. A unique attribution requires additional interventions.

The teaching pulses do affect some outcomes, but the broad changes also occur
without them. For example, baseline vertical reward stimulation delivers 270 PAM
spikes while retaining the same recorded phase weight summaries as no pulse.
Expanded vertical reward changes 65 connections versus 60 without reward.
Matching scalar summaries alone do not prove identical weight vectors.

## Input and electrical-state sensitivity

For the previously successful mapping 1 checkpoint, vertical must be rejected
and horizontal accepted. The following are frozen evaluations:

| Input/state | Vertical right-minus-left Hz | Horizontal right-minus-left Hz | Mapping 1 accuracy |
| --- | ---: | ---: | ---: |
| Original centered cues | -4 | +8 | 100% |
| Shift cues right by one pixel | +2 | +10 | 50% |
| Shift cues down by four pixels | +2 | +6 | 50% |
| Precede original cues with 500 ms blank | +4 | +2 | 50% |

Both spatial changes and the warmup remove the retained correct vertical choice.
They preserve the cue's orientation; thus the checkpoint does not demonstrate a
robust orientation category under these tested perturbations.

Strong activity sensitivity also predates learning. Untrained vertical shifts
from 17 KC spikes / four active KCs to 2,917 / 1,392 after a one-pixel horizontal
shift, and the decoder changes from +8 Hz accept to 0 Hz timeout. Untrained blank
input alone produces 2,320 KC spikes / 1,355 active KCs. Therefore broad KC
recruitment is not unique to the learned checkpoint and should not, by itself,
be labeled a learned representation or pathological activity.

Learned mapping 0 remains at 50% for all tested paired cue variants. Shuffled
mapping 1 remains at 50% under a one-pixel horizontal shift but falls to 0% under
the four-pixel vertical shift or blank warmup: vertical is accepted and horizontal
times out. Blank-only conditions have no classification target and must not be
scored as cue-learning accuracy.

## Selective memory restorations

These interventions all start from learned mapping 1:

| Restored target set | Selected edges | Vertical Hz | Horizontal Hz | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| None | 0 | -4 | +8 | 100% |
| MBON05 | 1,999 | -2 | +8 | 100% |
| MBON11 | 4,184 | 0 | +8 | 50% |
| MBON03 | 616 | -4 | +8 | 100% |
| Targets with at most two direct DAN contacts | 11,991 | +6 | +4 | 50% |
| Original MBON07/11 targets | 7,835 | +2 | +8 | 50% |
| Added targets | 26,414 | +8 | +8 | 50% |

MBON03 restoration preserves both complete nominal spike hashes. MBON05,
MBON11, and original-target restoration preserve the horizontal spike hash but
change vertical activity. Restoring added targets recovers both complete
untrained spike hashes, despite retaining memory changes in the original target
set. Those retained original-target changes alone have no observed effect on
these two reset-state neural trajectories.

Restoring weakly supported targets removes the correct vertical choice and
reduces both cue responses to 16 KC spikes / four active KCs. The successful
checkpoint therefore depends on part of the exploratory extension whose DAN
support is very weak. Restoring the original target set also removes success,
so the original and added memory changes interact. Neither set's necessity under
this particular restoration establishes sufficiency or a unique circuit path.

High KC activity alone does not explain the correct motor decision: restoring
original targets leaves 3,250 vertical KC spikes but changes rejection to
acceptance. The original cue's -4 Hz rejection also survives MBON05 restoration
at the -2 Hz decision boundary, showing limited margin.

## Interpretation limits

- Phase L1 values compare each phase's start and end. Summing them is not the
  total integrated magnitude of all 10 ms updates, nor an attribution of final
  weights to separate causes. Pulse-minus-no-pulse scalar differences are not
  distances between the resulting weight vectors.
- The phase suite locates the burst during the blank interval. A same-cue
  continuation comparison is needed to establish whether the visual transition,
  elapsed time, prior plasticity, or their interaction causes it.
- `freeze_settle` in the training suite freezes both learning and passive
  relaxation of latent efficacy into expressed weight. It does not isolate only
  the learning-rule drive.
- These few deterministic inputs and post-hoc restorative interventions do not
  estimate population generalization, prove biological fidelity, or establish
  that a particular neuron type always has the observed role.
- The prior pilots confounded label mapping with training order. The crossed
  training suite, rather than these checkpoint tests, is needed to assess that
  explanation.

The retained mapping 1 result is real for its exact input and reset condition,
but is sensitive to small input changes and depends on the exploratory plasticity
extension. Level 1 has not met its existing two-mapping progression gate.

## Follow-up audit: crossed training and transition controls

The completed `training.json` and `transition.json` suites resolve two questions
left open above. This follow-up also used read-only analysis and ran no neural
simulations.

### Verification

- Training's 120 rows and transition's 24 rows exactly match their respective
  progress JSONL files.
- Training retains source SHA-256
  `d9bfd88ad8b0ae495a28ba371017cb1f18e2bebebaea5ef6f81137f49536353a`,
  matching the source committed in `e8df3db`. The running process had loaded this
  version before the transition suite was added to the file.
- Transition records source SHA-256
  `eaed8d77025fbf785c710ff88f8e7f926d8d7cc762f467fe19a8d964a5b9d753`,
  matching the source inspected for this follow-up. Its recorded starting HEAD
  is `e8df3db`; the later source hash distinguishes it from the earlier suites.
- Both normal training reproductions (order 0/mapping 0 and order 1/mapping 1)
  match all eight original training cues, actions, correctness values, and
  delivered pulses. Their four final cue observations match both corresponding
  original full-network spike hashes and changed-edge counts exactly.
- Without external feedback, each order's two mappings give identical final
  full-network spike hashes for each cue, as expected when labels cannot affect
  neural stimulation. This checks label independence of the observed outputs;
  these diagnostics do not save final weight-vector hashes for comparison.
- All eight paired transition prehistories match exactly in the recorded
  observation/continuation fields before the final interval differs. Every
  fully frozen transition row reports zero changed connections and zero weight
  movement.

### Crossed training: one success across four order/mapping combinations

| Training condition | Order 0, mapping 0 | Order 0, mapping 1 | Order 1, mapping 0 | Order 1, mapping 1 |
| --- | ---: | ---: | ---: | ---: |
| Normal outcome feedback | 50% | 50% | 0% | 100% |
| No external feedback | 50% | 50% | 50% | 50% |
| Freeze final 250 ms | 50% | 50% | 50% | 50% |

Order 0 is H,V,H,V,H,V,V,H and order 1 is V,H,V,H,V,H,V,H. Each has four examples
of each cue. The mapping 1 success disappears with the other order, and mapping 0
does worse under order 1. This establishes sensitivity to the tested interaction
of labels and presentation order; two schedules do not identify a universal
order effect or estimate how often success would occur.

Without external feedback, 14,027 connections change under order 0 and 14,677
under order 1, while accuracy remains 50%. Thus changing many connections is
not evidence of learning the assigned labels. The normal successful condition
differs from no-feedback and frozen-settle controls, so external feedback and
the final interval's memory dynamics matter to that particular retained result.
This does not establish a robust learning procedure.

Freezing the final interval does not solve either mapping in either order.
It still permits endogenous and feedback-driven learning in the preceding
700 ms, and it freezes passive memory relaxation as well as new plasticity in
the last 250 ms. The result is therefore an intervention on that whole interval's
memory dynamics, not an isolated test of one term in the plasticity rule.

### Transition control: the late burst needs neither cue offset nor plasticity

All transition conditions begin from untrained memory, receive no external
teaching pulses, and observe the same cue for 700 ms. The final 250 ms either
keeps that cue visible or switches to blank. Horizontal-cue results for this
700-950 ms interval are:

| Plasticity | Final image | KC spikes | Active KCs | Weight L1 movement |
| --- | --- | ---: | ---: | ---: |
| Enabled | Blank | 3,469 | 1,380 | 2,430.040039 |
| Enabled | Continue horizontal cue | 3,673 | 1,462 | 2,474.229980 |
| Fully frozen | Blank | 2,744 | 1,404 | 0 |
| Fully frozen | Continue horizontal cue | 2,652 | 1,363 | 0 |

Vertical produces only eight KC spikes in each corresponding final interval.
The horizontal burst therefore does not require a switch to blank, external
reinforcement, or changing weights. It exists in the frozen simulator under
continuous cue presentation. The interval's visual content and plasticity still
alter its magnitude and motor output; those factors are not irrelevant.

This corrects any interpretation that the blank transition itself causes the
broad burst. The original phase suite located substantial plasticity in the
700-950 ms interval, and the transition controls show that this is also where
the existing simulator can express a broad delayed response to sustained input.

The task commits its action from the first 500 ms, when only four KCs are active
for each initial cue, but large populations and extensive plasticity appear
later. This is an observed mismatch between the decision window and the neural
activity dominating later updates. Because the rule does not explicitly retain
action-specific eligibility, these late changes are not automatically credit
for the earlier chosen action. The relative contributions of delayed network
dynamics, sensory adaptation, and recurrent pathways remain to be established.

These findings motivate measuring the full temporal response before changing
the training protocol. They do not show that a longer observation window fixes
conditioning: that would change cue presentation, the chosen action, feedback
timing, eligibility, and potentially the subsequent trajectory, requiring a new
controlled experiment under both mappings. The existing Level 1 gate remains
unpassed.
