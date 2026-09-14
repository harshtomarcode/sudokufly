# Prospective selective Undo-memory ablation

Freeze and commit this addition before inspecting any ablation outcomes. Keep the ongoing 007 protocol, its controls, all declared gates, and its final summary unchanged. This adds a mechanism test; it does not repair or reinterpret a failed gate. No training, parameter changes, cue changes, new policies, or heldout inspection are permitted.

## Question and scope

Does the newly learned Undo association improve trap recovery **within the already trained placement policy**? The paired memory may accept more locally legal but ambiguous moves, while a weak warm control may avoid those moves and finish by repeated constrained placements. Consequently, a successful selective ablation could establish a conditional contribution of learned Undo to this particular trained policy, not that learning is necessary for puzzle completion, or that the trained policy outperforms the warm controls.

Use all four paired source conditions from completed, committed 007. Do not choose conditions, boards, or views using Undo frequency or successful recovery. Preserve and report the complete warm-control results, including any control that solves every board.

## Intervention fixed before results

1. Load the exact final paired 007 checkpoint for each seed and mapping. Bind its checkpoint SHA256, committed 007 summary/source hashes, decoder, templates, input manifest, KC-bank IDs, case manifest, and unchanged driver to this assay.
2. Compute the intervention mask solely from anatomy and the previously frozen Undo-bank identity: among the original 7,835 plastic edges, select **every edge whose presynaptic KC belongs to the 256 Undo KCs**. Both readout compartments are included. The expected bank contains 892 eligible edges; verify rather than silently accept a different count. Select all eligible Undo edges, not just changed edges, a particular pattern, a favorable compartment, or a score-derived subset.
3. Replace only those selected edge weights and their aligned `u` and `w` entries with the exact corresponding values in that condition's original paired Step3 checkpoint, before any Undo training. Do not replace the rest of the Step3 memory, restore placement weights, reset latent memory wholesale, use the already trained 003 checkpoint, zero neural currents, clamp the Undo action, or disable the Undo menu.
4. Keep every other weight and latent-memory entry bit-for-bit equal to final paired 007. Full network anatomy, nonplastic weights, tonic currents, stimulus strengths, and decoder stay fixed. Reset electrical state between stimuli exactly as in 007 and evaluate with all weights and latent memory frozen.

Use edge identity to align checkpoint arrays, not an assumed slot order. Save the selected global edge indices, selected slots, presynaptic KC IDs, old/retained/replaced array hashes, and resulting hybrid checkpoint. Verify that all masks and shapes align, the Undo bank is disjoint from the original and occupancy-specific placement banks, and no input other than the 16 Undo inputs directly stimulates its KCs. Source `u/w` values should be verified from the original checkpoint; do not assume they are zero.

## Frozen neural checks

For each condition, first remeasure all 165 inputs in the intact loaded checkpoint and reproduce committed 007 responses exactly. Then measure all 165 in the selective-erasure state using the same ordering, durations, bins, and electrical resets. Then restore the exact paired arrays and remeasure all 165 inputs against intact 007 again. This is 495 physical evaluations per condition, 1,980 total in 12 fully frozen batches; no training evaluations are added.

Within each intact/erased batch, require unchanged full-network weights and unchanged `u/w`. Across states, verify that every changed weight or latent-memory entry lies inside the fixed Undo edge mask, and every selected value equals original Step3.

For all **149 non-Undo physical inputs**, require exact equality of spike hashes, output rates/counts, decision scores/actions, KC/DAN spike counts, and complete traces against intact 007. The global memory hashes will intentionally differ after erasure; validate each against its own frozen state rather than demanding equality across the two states. Any changed non-Undo neural response invalidates the simple claim that this intervention leaves placement behavior fixed; report the effect but do not call it isolated Undo causality.

Report all 16 Undo responses before and after erasure, balanced accuracy, both class recalls, raw outputs, margins, and changed decisions. Require erased Undo neural behavior to match the existing original-Step3 references exactly, apart from global memory hashes. Differences fail the isolation gate and could reveal network interactions despite a disjoint direct-input mask. Reconstruct the intact arrays afterward, require their original full W/u/w hashes, and remeasure all 165 inputs exactly as a restoration check.

## Board evaluation and primary effect

Use the same 160 development boards in all base/shift/small views, for all four conditions, through the unchanged renderer, pixel encoder, and fixed menu/stack driver. Replay both intact and selectively erased frozen response tables: 4 × 2 states × 160 boards × 3 views = 3,840 episodes. The intact replay must reproduce 007 episode actions and endings exactly. Log every action and ending in compressed records.

Primary denominator: the original **64 trap boards per view** (32 three-blank traps plus 32 four-blank traps), including paired failures and episodes without an Undo. For every condition and every view, require an absolute reduction of at least **25 percentage points** in trap solve rate after selective Undo erasure. Also report each trap stratum separately, paired per-board solved→failed and failed→solved transitions, all five original strata, and all 160 boards. Do not count three views as independent neural replications: they reuse the same finite sensory inputs and measured responses.

This prospective 25-point mechanism criterion supplements, and cannot replace, the original 007 requirements: the existing Undo/new-placement learning gaps, whole-placement gap, strict original-memory retention, absolute per-class placement/Undo thresholds, and per-stratum/view recovery thresholds must still pass. Intact Undo balanced accuracy must be at least 90%, and selective erasure must reduce it by at least 25 percentage points. If Undo decisions remain unchanged or non-Undo neural responses change, the intended mechanism test has not isolated the proposed cause.

Report both successful placements and undo events descriptively, but never select the evaluated board subset according to those outcomes. A large drop on a post hoc subset of episodes that happened to Undo is not the primary result.

## Interpretation and heldout rule

If all original development gates and the added isolation/effect requirements pass, the supported claim is: “With trained placement judgments held fixed, restoring only Undo-associated synapses to their pretraining state reduced trap recovery by at least 25 points in every source condition and view.” The direct warm-control comparison must be reported beside that claim, including equal or better completion by controls.

If the effect is smaller, mixed, or the isolation check fails, report that result. Do not alter the threshold, choose favorable cases, change the branch/menu order, retrain, or replace the warm controls. High puzzle completion alone remains insufficient evidence that learned Undo was necessary.

Required execution order: finish and commit passing 007 development; run this 008 development assay; audit and commit passing 008 development; run unmodified 007 heldout; only after 007 heldout also passes and is committed, run 008 heldout with the same frozen paired/erased states on those 160 heldout boards. Require both passing 008 development and passing 007 heldout as inputs to 008 heldout. The same thresholds and denominators apply, with zero learning. Reconstructed erased checkpoints and all neural responses must reproduce committed 008 development exactly. A heldout mechanism claim and full-stage completion with causal recovery require this final selective-ablation criterion too. Historical 007 summaries remain unchanged and its completion flag continues to mean only its original gates.

## Execution

The controlled development input is committed at `7d1f079`. Preserve its
original gates and results. This additional file keeps the 007 runner unchanged
for its already frozen confirmation protocol.

```sh
.venv/bin/python ablate_undo.py --source experiments/level-05/007-controlled-recovery/development --out experiments/level-05/008-selective-undo-erasure/development
# After passing008development is committed and007heldout passes and is committed:
.venv/bin/python ablate_undo.py --source experiments/level-05/007-controlled-recovery/heldout --split heldout --development experiments/level-05/008-selective-undo-erasure/development --out experiments/level-05/008-selective-undo-erasure/heldout
```
