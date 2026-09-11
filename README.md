# sudokufly

Learn inside a simulated fruit-fly connectome, with Sudoku as the eventual goal.
Level 1 implements a visual cue conditioning experiment using the full retained
MaleCNS graph: 166,700 neurons and 25,582,938 directed connections. The action
decoder is fixed; there is no external trained output layer or policy.

## Setup

Requires Python 3.11+ and a C++17 compiler available as `c++` (Apple Command Line
Tools on macOS). Run from this repository. The four packages in
[requirements.txt](requirements.txt) are the pinned neural dependencies;
trading dependencies are unnecessary.

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p .upstream
git clone https://github.com/nftechie/stonkfly.git .upstream/stonkfly
git -C .upstream/stonkfly checkout --detach 78ef3e05ab0fa086032098558d893667068944a0
PYTHONPATH=.upstream/stonkfly STONKFLY_DATA=data .venv/bin/python -c 'from stonkfly.data import prepare; prepare()'
```

Preparation downloads about 1.1 GB, verifies the released source checksums,
imports the graph, and checks its arrays against the upstream locks. Prepared
data occupies about 1.6 GB. The native kernel compiles automatically on first
use. Keep `.upstream/`, `.venv/`, `data/`, and `runs/` out of Git.

## Run Level 1

```sh
# Frozen cue responses and explicit reward/aversive pulse diagnostics.
.venv/bin/python sudokufly.py --probe

# Controlled pilot: eight training trials per arm and target mapping.
.venv/bin/python sudokufly.py --trials 8

# Same Level 1 task, with more existing connections allowed to learn.
.venv/bin/python sudokufly.py --plasticity expanded --trials 8
```

`--trials 8` is the default. Each invocation writes a new timestamped directory
under `runs/`; `--out PATH` selects a directory that must not already exist.
See `--help` for parameters. Results include the exact protocol and source hash,
cue images, per-trial activity and memory measurements, plastic-weight
snapshots, and a `summary.json` with artifact hashes. These snapshots preserve
selected weights and `u/w` at trial boundaries, not mid-trial electrical state.
The probe never trains. `--plasticity baseline` is the default and permits
learning on 7,835 existing KC→MBON07/11 connections.

Opt-in `--plasticity expanded` permits learning on 34,249 positive existing
connections from Kenyon cells to 44 mushroom-body output neurons: **4.37× as
many plastic connections**. It retains every baseline edge and its original
modulation gain. Additional targets qualify with even one direct contact from
the same 17 PAM11/PPL101 dopamine neurons; their gains use normalized contact
fractions. Weakly supported targets can therefore receive unit total gain.
This is an unvalidated anatomical proxy for dopamine modulation. Both variants
use the same complete graph, stimuli, learning rule, and fixed action decoder.

## Protocol and interpretation

- **Observation:** centered vertical and horizontal stripe images have exactly
  the same pixel brightness histogram. The fixed retinal projection can still
  sample them differently; sampled-input statistics are recorded.
- **Decision:** mean DNp20 right-minus-left activity over 500 ms selects accept
  at +2 Hz or above, reject at -2 Hz or below, and timeout otherwise. There is
  no DNpe017 gate. These are engineered meanings assigned to neuron activity.
- **Teaching:** after committing a decision, correctness selects a 200 ms PAM11
  reward or PPL101 aversive stimulation pulse. Timeouts count as errors. The
  existing upstream local plasticity rule changes only the selected KC→MBON
  memory connections. The remaining network and decoder are fixed.
- **Counterbalancing:** two opposite target mappings exchange which cue means
  accept. Each arm starts from baseline weights and sees a balanced, seeded cue
  schedule. Electrical state and activity traces reset between trials while
  learned synaptic weights and their `u/w` memory states persist within an arm.
- **Controls:** the frozen arm receives the learned arm's exact teaching pulses;
  the shuffled arm learns from a seeded permutation of those same pulses,
  preserving their total dose. An unchanged shuffle cannot pass the gate.
- **Evaluation:** learning, passive memory relaxation, and weight writes are
  frozen; teaching pulses are absent. Each cue is repeated from the same reset
  state to check determinism. Erasing plastic weights and `u/w` must reproduce
  baseline activity exactly; the frozen control must also recover baseline.

The exploratory progression gate requires both target mappings to achieve
balanced accuracy ≥75%, improve by ≥25 percentage points over baseline, frozen,
and shuffled controls, and satisfy the control checks. Repeated deterministic
trials are not independent training replicates. Even passing this gate would
establish only a small cue-conditioning result; Sudoku, generalization to unseen
stimuli, and an advantage from fly wiring require later experiments.
Work stays at Level 1 until its gate passes; Level 2 has not started.

## Results

Level 1 experiment 001 completed on 2026-09-10: **the behavior gate failed**.
All 88 neural trials completed, including both target mappings and controls.

| Condition | Mapping 0 accuracy | Mapping 1 accuracy |
| --- | --- | --- |
| Untrained baseline | 50% | 50% |
| Learned | 50% | 50% |
| Frozen / shuffled / erased | 50% | 50% |

Training changed 2,919 and 2,963 of the 7,835 eligible connections, but the
fixed decoder continued to accept both cues. Frozen and erased weights recovered
the baseline spike traces exactly. This establishes an operating experimental
loop, not learned cue discrimination. Sudoku levels have not started.

Experiment 002 expanded the plastic set to 34,249 connections. The learned arm
scored **50% / 100%** across the two opposite mappings; frozen, shuffled, and
erased controls stayed at 50% in both. One mapping passes the exploratory gate,
but **Level 1 remains unpassed** because both mappings must pass. Experiment 001
above remains the preserved baseline result.

Experiment 003 [diagnoses the failure](experiments/level-01/003-diagnosis/README.md).
The horizontal cue drives a delayed firing burst even without feedback, a blank
transition, or plasticity. Decisions sample the first 500 ms while learning
continues through the much stronger late response. The original 100% result
falls to 50% under the other training order or either tested small image shift.
Removing external feedback still changes thousands of weights; freezing the
blank interval alone leaves all conditions at 50%. Memory storage works, but
reliable task learning has not been established.

Experiment 004 [demonstrates direct neural association learning](experiments/level-01/004-direct-conditioning/README.md):
two disjoint KC stimulation patterns acquire opposite valences in both tested
training orders. The fixed MBON comparator correctly decodes all eight distinct
trained cue decisions. Frozen, no-feedback, inconsistent-pairing, and erased
controls time out. Exactly 58 appropriate existing connections change per paired
run, with their efficacies reduced by about 34%. This uses direct stimulation,
an explicitly calibrated constant output current, and Pavlovian pairing;
**visual Level 1 remains incomplete**.

See the [Level 1 experiment record](experiments/level-01/README.md) for the command,
evidence, interpretation, and next experiment. Preserve each experiment in its
own numbered directory; commit its code and results together.

## Sources

The neural runtime is the pinned [Stonkfly implementation](https://github.com/nftechie/stonkfly/tree/78ef3e05ab0fa086032098558d893667068944a0),
adapted upstream from Doomfly, copyright © 2026 nftechie and DOOMFLY contributors.
Its [MIT license](https://github.com/nftechie/stonkfly/blob/78ef3e05ab0fa086032098558d893667068944a0/LICENSE)
is preserved in the separate checkout. [MaleCNS v1.0](https://male-cns.janelia.org/download/)
is separately downloaded data from the MaleCNS collaboration and contributors,
under CC BY 4.0; its attribution and publication citation requirements remain.

[RESEARCH.md](RESEARCH.md) preserves the historical source audit and proposed
progression toward Sudoku. Its initial research-only status describes the audit
date; this README and recorded runs describe the implemented Level 1 experiment.
