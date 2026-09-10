# Level 1 — visual cue conditioning

Status: implementation and first controlled pilot complete; learning gate failed.
Later Sudoku levels have not started.

## Experiment 001: fixed visual interface

Run on 2026-09-10 using the full retained MaleCNS network and the pinned Stonkfly
neural implementation. Execution took 151.26 seconds including model loading,
excluding prior data verification/preparation. No parameters or decoder were
changed after observing the pilot's results.

```sh
.venv/bin/python sudokufly.py --trials 8 --seed 20260910 --out runs/level-01-reproduction
```

The committed run is [001-visual-cues](001-visual-cues/). Its
[protocol](001-visual-cues/protocol.json) records the exact source hash, dependency
versions, upstream commit, input hashes, neural identities, and gate criteria.
The [summary](001-visual-cues/summary.json) hashes its artifacts. Detailed
[trial records](001-visual-cues/trials.jsonl) and six compressed memory snapshots
are retained alongside both stimulus images.

Each of two opposite cue-to-action target mappings received eight balanced
training trials in each arm. Forty frozen evaluation trials plus 48 training
trials produced 88 total trials. Each evaluation repeats the two cues from fresh
electrical state: those repeats check determinism, not statistical replication.

| Condition | Mapping 0 accuracy | Mapping 1 accuracy | Changed edges, mapping 0 / 1 |
| --- | --- | --- | --- |
| Untrained | 50% | 50% | 0 / 0 |
| Learned feedback | 50% | 50% | 2,919 / 2,963 |
| Frozen weights | 50% | 50% | 0 / 0 |
| Shuffled feedback | 50% | 50% | 2,958 / 2,943 |
| Erased memory | 50% | 50% | 0 / 0 |

Both cues produced an 8 Hz right-minus-left DNp20 difference, hence the fixed
controller selected accept throughout evaluation. Training did not change that
readout. The vertical and horizontal inputs elicited distinct, repeatable KC
activity (17 versus 16 spikes over the initial 500 ms). Their pixel histograms
match exactly, while sampled retinal means differ slightly, as recorded.

The frozen arm and memory erasure reproduced every baseline evaluation spike
hash. No nonplastic connections changed. Evaluation delivered no reinforcement
and froze both effective and latent memory states. Shuffles were distinct and
preserved the learned arm's total reward/aversive pulse counts and durations.

Both learned runs reached efficacy bounds on a few edges: three at the lower
bound in each mapping, and three/two at the upper bound. More training or higher
gain should not be assumed to fix the motor bias.

## Decision and next experiment

Keep this failed pilot as the baseline. The next Level 1 experiment should test
whether targeted changes to the permitted memory connections can influence the
fixed motor readout, and inspect sensory encoding and firing dynamics. A lack of
action change in this pilot does not prove the pathway is disconnected.

Any changed input mapping, readout, neuron parameters, or learning rule belongs
in a new numbered experiment with its own committed protocol. Progress to symbol
comparison only after the cue-learning gate passes. This pilot establishes no
Sudoku reasoning, biological replication, or advantage of the anatomical wiring.
