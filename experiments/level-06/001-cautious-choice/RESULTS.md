# Cautious-choice development result

**The predeclared pilot gate passes under both answer mappings. Step 6 is not
complete.** Runner `4402991efd02d614dc899548fe5d2586fbb53965` ran for 591.72 seconds
from the Step 5 paired history with seed 20260919. The first passing checkpoint
is epoch 4 in both mappings. The [prospective protocol](README.md) is unchanged;
the [summary](development/summary.json) binds the saved artifacts by hash.

The new teaching target accepts a candidate only when it is absent from three
distinct peer symbols, and defers otherwise. It changes 24 nonempty judgments
at peer counts one and two, retaining the other 36 placement judgments and all
16 Undo judgments. Learning uses the same 7,835 existing synapses and dopamine
rule. Sensory routing and the binary readout remain fixed.

At each board state, a supplied selector assesses all four digits in every
empty cell and selects the highest accepted, mapping-oriented neural score.
Ties use cell order, then digit order. The selector receives no legality mask,
peer count, singleton flag, teacher label or solution. It stops if no offer is
accepted; this pilot executes no Undo or fallback guess. Solutions enter only
post-run grading.

## Selected checkpoints and matched controls

All rows below use the same new selector and the same 160 development boards.
“Wrong” counts executed placements that disagree with the unique solution.
Judgment columns count correct explicit responses; timeouts are incorrect.

| Mapping 0 arm | Solved / 160 | Wrong | Changed / 24 | Retained / 36 | Undo / 16 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Paired | 160 | 0 | 24 | 36 | 16 |
| Frozen | 128 | 32 | 0 | 36 | 16 |
| No feedback | 127 | 33 | 0 | 32 | 16 |
| Inconsistent feedback | 122 | 38 | 0 | 35 | 16 |

| Mapping 1 arm | Solved / 160 | Wrong | Changed / 24 | Retained / 36 | Undo / 16 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Paired | 160 | 0 | 24 | 36 | 16 |
| Frozen | 114 | 46 | 0 | 36 | 16 |
| No feedback | 114 | 46 | 0 | 36 | 16 |
| Inconsistent feedback | 130 | 30 | 0 | 35 | 16 |

Both paired runs make exactly 512 placements, all correct and locally forced,
and solve 32/32 in each of the five existing blank-count/easy/trap strata.
The prespecified contrast balances 24 changed negatives against four retained
forced positives: paired accuracy is 100%, versus 50% for every control, a
50-percentage-point gap. All four forced positives remain correct in every arm.
The four conceptual empty-peer contexts alias one silent input and time out;
they remain outside learning claims.

Earlier checkpoints remain recorded. Mapping 1 already solves 160/160 at epoch
1 with only 2/24 changed judgments correct. Both mappings solve 160/160 at
epoch 2 with only 20/24 changed judgments correct. Epoch 3 reaches 23/24;
epoch 4 is the first to meet every judgment and sequence gate. Board completion
alone was insufficient to select a checkpoint.

## Comparators and cost

Before new teaching, the original Step 5 memory under the new selector solves
128/160 and 114/160, with 32 and 46 wrong placements respectively. Frozen
controls reproduce those responses and outcomes. The gain therefore cannot be
attributed to the new selector alone.

Under its original ascending menu, the Step 5 paired policy solved 159/160
development boards, making 64 wrong placements and executing 65 Undos. The
favorable Step 5 warm controls already solved 160/160 with that old menu and no
Undo by postponing ambiguous moves. This pilot demonstrates an improvement to
the inherited paired policy under a stated selector, not superiority to every
earlier control or proof that further learning was necessary to solve this set.

The paired pilot assesses **4,480 offers** per mapping, compared with **2,183
total placement/Undo offers** for the old paired policy. The source memories
under the new selector assess 4,352 and 4,288 offers; some boards stop early.
Reduced wrong placements do not imply fewer neural evaluations or lower compute.

## Integrity and independent audit

Every evaluation freezes weights, both latent memory arrays and passive
relaxation; observations include no teaching pulses. Restoring the inherited
Step 5 weights and latent state reproduces all 165 frozen neural responses
exactly. Runner assertions verify that nonplastic weights remain unchanged.
Controls replay the paired teaching mask and phase schedule. Nonfrozen update
windows total 62.55 seconds in mapping 0 and 69.60 seconds in mapping 1; frozen
controls have zero update exposure. Actual dopamine doses are saved: mapping 0
has a small paired/inconsistent difference in compartment allocation from the
short correction trials, so equal per-compartment dose is not claimed.

The [independent audit](final-audit.json) verifies all 25 artifact hashes,
2,432 training trials, 2,970 neural records, 193,050 spike bins, 2,560 episodes,
70,396 candidate offers and 7,396 distinct rendered images. It reconstructs
readout rates, decisions, selection, board transitions and summary results.
These are repeated runs on 160 distinct boards, not 2,560 independent puzzles.
Selected-cell traces verify readouts, not the whole-network spike hash;
training-wide nonplastic integrity relies on the committed runner's full-weight
restoration assertions because checkpoints store only plastic edges.

## Demo and scope

The default **Careful choices** replay uses mapping 0, epoch 4 and development
case `b4-0009393db5453f62`, the first lexicographic case in the existing four-blank
trap stratum. This visual example was selected after training to show ambiguous
offers being deferred before forced placements; the stratum predates this pilot,
and no experimental cases, gates or results changed. It shows four chosen
placements and makes all 40 assessments inspectable. Activations and edge weights
come from that exact frozen checkpoint; the original three Step 5 replays remain
available.

This is one inherited training history under two answer mappings, on the existing
finite sensory representations and assisted 4×4 boards with 2–4 blanks. The
pilot learns local deferral, not calibrated confidence, visual recognition or
global planning. There was **no reserved-puzzle evaluation**. Independent-history
replication and prospectively specified confirmation remain future work;
`stage6_complete` remains false.
