# Level 1 — visual cue conditioning

Status: two controlled pilots recorded; the overall learning gate has not passed.
Experiment 002 passes one of the two opposite mappings. Later levels have not
started and will remain blocked until Level 1 passes.

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

## Experiment 002: expanded memory connections

Run on 2026-09-10; execution took 167.91 seconds including model construction,
excluding prior data verification/preparation. The failed baseline was committed
first as `6318497`. The second experiment changes the plasticity scope, preserving
the original cue schedule, timing, rate rule, full initial graph, stimulated DANs,
fixed decoder, and baseline modulation gains.

```sh
.venv/bin/python sudokufly.py --plasticity expanded --trials 8 --seed 20260910 --out runs/level-01-expanded-reproduction
```

The expanded selection has **34,249** positive existing KC→MBON edges, versus
7,835 originally: 4.37× as many. Its 44 MBON targets receive at least one direct
contact from the same 17 PAM11/PPL101 cells. New modulation gains normalize those
contacts within each target, including weakly supported targets. This is an
exploratory anatomical proxy, not validated compartment physiology. No graph
connections or neurons were added; the entire graph was already simulated.

See the [protocol](002-expanded-memory/protocol.json),
[summary](002-expanded-memory/summary.json), and
[trial records](002-expanded-memory/trials.jsonl). All 88 trials completed.

| Condition | Mapping 0 accuracy | Mapping 1 accuracy | Changed edges, mapping 0 / 1 |
| --- | --- | --- | --- |
| Untrained | 50% | 50% | 0 / 0 |
| Learned feedback | 50% | 100% | 14,800 / 15,065 |
| Frozen weights | 50% | 50% | 0 / 0 |
| Shuffled feedback | 50% | 50% | 14,875 / 14,836 |
| Erased memory | 50% | 50% | 0 / 0 |

In mapping 1 (vertical→reject, horizontal→accept), learned readouts were −4 Hz
and +8 Hz, respectively. This retained choice difference disappeared after
erasing memory, and the frozen/shuffled controls did not reproduce it. Mapping 1
therefore passes the declared exploratory gate. Mapping 0 still accepts both
cues at +2 Hz and fails. The overall gate requires both, so **Level 1 is not yet
passed**. Averaging the mappings into a 75% headline would obscure this failure.

Expanded plasticity caused large changes in recurrent activity. Mapping 1's
learned vertical response had 3,526 KC spikes versus 17 initially. This motivates
checking physiological stability and specificity; it is not itself a measure of
better learning. One learned and one shuffled training trial timed out; all final
evaluations produced actions. These are tiny deterministic cue assays, not a
generalization or statistical validation study.

## Decision and next experiment

Preserve both pilots. Expansion establishes that the permitted memory changes
can influence the fixed motor readout in this setup. The next Level 1 experiment
should investigate why the opposite target mapping fails, test repeatability
under new training orders, and examine the large changes in firing activity.
More connections alone have not completed the task.

Any changed input mapping, readout, neuron parameters, or learning rule belongs
in a new numbered experiment with its own committed protocol. Progress to symbol
comparison only after the cue-learning gate passes. This pilot establishes no
Sudoku reasoning, biological replication, or advantage of the anatomical wiring.
