# sudokufly

Learn inside a simulated fruit-fly connectome, with Sudoku as the eventual goal.
Experiments use the full retained MaleCNS graph: 166,700 neurons and 25,582,938
directed connections. The action decoder is fixed; there is no external trained
decision head or policy. The assisted visual cue experiment completes Step 1.
Step 2 evaluates comparison of four familiar symbols with explicit template
recognition and sensory pooling, while learning remains inside existing fly
synapses.

**Step 2 is complete for this assisted comparison task:** all 24 distinct
unseen two-row compositions are answered correctly under both answer mappings
and both fresh training orders. Controls score 0–8.33%, and erasing memory
restores baseline responses. See the [controlled results and audit](experiments/level-02/005-controlled-replication/README.md).

**Step 3 is complete for assisted one-blank 4×4 boards:** all 4,608 distinct
boards, four candidates and three renderings receive correct judgments under
both answer mappings and both saved Step 2 training histories. The frozen
reserved-family confirmation passes every gate; curriculum controls score
0–16.67%. These presentations share only 16 neural inputs. Correct additional
Step 3 feedback has not been shown necessary, and this does not establish
general Sudoku reasoning. See the [results and audit](experiments/level-03/010-curriculum-continuation/README.md).

**Step 4 passes the restricted assisted constraint-transfer test:** legal
judgments and isolated row, column and box conflicts are all answered correctly
under both mappings and both saved histories, including the reserved layouts.
The 10,752 highlighted board/target cases share 16 familiar neural inputs.
No new learning occurs; spatial relevance is supplied by the interface.
See the [results and limits](experiments/level-04/001-frozen-transfer/README.md).

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
Later model variants are evaluated separately; the original retinal/DNp20 gate
above remains failed. Experiment 005 passes cue learning under an explicitly
engineered visual adapter, allowing Step 2 symbol comparison to begin.

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
the baseline spike traces exactly. This established an operating experimental
loop, not learned cue discrimination; Sudoku levels had not started at that point.

Experiment 002 expanded the plastic set to 34,249 connections. The learned arm
scored **50% / 100%** across the two opposite mappings; frozen, shuffled, and
erased controls stayed at 50% in both. One mapping passes the exploratory gate,
but **the original retinal variant remains unpassed** because both mappings must pass. Experiment 001
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
**that experiment did not complete visual Level 1**.

Experiment 005 [passes image-derived cue learning](experiments/level-01/005-image-adapter/README.md)
using a fixed random pixel-to-KC adapter and the calibrated MBON readout. Both
opposite assignments score 100% under both orders, including withheld thinner
and thicker bars. Controls do not reproduce the result; erasure restores exact
baseline activity. **Step 1 is complete for this assisted visual variant.**
This does not validate native retinal processing; the earlier failures remain
preserved. Step 2 follows in the [symbol-comparison experiment record](experiments/level-02/README.md).

See the [Level 1 experiment record](experiments/level-01/README.md) for the command,
evidence, interpretation, and next experiment. Preserve each experiment in its
own numbered directory; commit its code and results together.

## Run Step 2

```sh
.venv/bin/python compare_symbols.py probe --task symbols --encoder templates --teaching bidirectional --eta 0.00075 --epochs 4 --threshold-hz 2 --encoder-seed 20260917 --training-seed 20260919 --out runs/step2-probe
.venv/bin/python compare_symbols.py train --task symbols --encoder templates --teaching bidirectional --eta 0.00075 --epochs 4 --threshold-hz 2 --encoder-seed 20260917 --training-seed 20260919 --reference runs/step2-probe --out runs/step2-train
```

Use new output directories for each run. The probe must use the same source
and parameters as training. `pilot` replaces `train` for a development run
with one order and only paired teaching; a pilot cannot pass the controlled gate.
The exact recorded Step 2 experiment used commit `5aa3db1`. Current code has
equivalent execution with clarified docstrings; its byte hash differs, so use
a newly generated probe with current code rather than the archived reference.

Training presents one row symbol and a candidate. Recall presents two distinct
row symbols and a candidate; the fly must indicate whether it repeats one
already present. All 16 atomic pairs are taught, but the 24 unordered two-row
compositions are withheld from reinforcement. Both opposite answer mappings
and two training orders are tested. The fixed template parser supplies symbol
recognition and row pooling; the learned valences reside in existing KC→MBON
connections. No equality flag or solution enters the sensory encoder.

Teaching uses both timing directions of the unchanged upstream local rule:
cue-before-dopamine weakens one compartment, and dopamine-before-cue strengthens
the other. Every trial gives one pulse to each compartment; the target label
determines their timing. This is supervised neural conditioning with an
engineered interface, not natural fly training or Sudoku solving.

The completed replication changes 909 existing synapses per learned state.
Both weakening and strengthening matter: earlier random features failed, and
template routing with weakening alone reached 79.17% in one mapping. The
bidirectional timing protocol reaches 100% in all four fresh conditions with
at least 3.125 Hz of margin beyond the unchanged decision threshold.

Repeated renderings and row reversals that produce identical KC inputs are
recorded as explicit aliases of one measured frozen response. Reports separate
distinct neural inputs from rendered presentations. Source hashes, protocols,
raw records, control results, and memory snapshots accompany every experiment.

## Run Step 3

The assisted one-blank task presents a full valid 4×4 board, a highlighted
blank, and each candidate digit in turn. The fixed template interface reads
the blank's row and drives three familiar symbol-pair populations. The neural
readout must explicitly accept the completing digit and reject the other three;
timeouts are incorrect. A fixed first-accept scan separately measures completion.

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --train-epochs 8 --teaching depression --control-history curriculum --out runs/step3-development
# Run only after every development gate passes; loading enforces that condition.
.venv/bin/python one_blank.py --split heldout --per-pair 8 --timing simultaneous --teaching depression --control-history curriculum --conditioning-source runs/step3-development --out runs/step3-heldout
```

Each original Step 2 arm continues its own saved learning history. Paired
training gives a post-cue dopamine pulse only after an incorrect or undecided
judgment; the existing local rule weakens recently active synapses. Every
evaluation freezes weights and latent memory. Both stage-specific and full
erasure must restore the corresponding earlier responses exactly.

The [Step 3 record](experiments/level-03/README.md) preserves every failed
variant and the [curriculum continuation](experiments/level-03/010-curriculum-continuation/README.md).
The task's 288 solved grids yield 4,608 one-blank boards. Development uses one
96-grid symmetry family, and confirmation reserves the other 192 grids.
All positions, all four candidates, and three renderings are covered. These
images collapse to only 16 neural inputs, including across the family split;
confirmation tests board coverage rather than new neural representations.

The stronger claim that correct additional Step 3 feedback is necessary remains
unsupported: [warm-start shuffled feedback](experiments/level-03/007-depression-conditioning/audit.md)
already reaches 83–92% when every control inherits the correct Step 2 memory.
Whole-curriculum controls test overall learning history. Template recognition
and target-row attention are engineered; this task cannot establish separate
row, column, and box reasoning or general Sudoku solving.

## Run Step 4

The isolated-constraint experiment presents a partial 4×4 board, a highlighted
empty target, and every candidate digit. It tests row-only, column-only and
box-only violations against legal cases with the same candidate elsewhere on
the board. Fixed geometric attention selects the target's row, column and box;
learned candidate judgments transfer from the frozen Step 3 memories.

```sh
.venv/bin/python constraint_transfer.py --split development --out runs/step4-development
# Only after all development gates pass and the source/results are committed:
.venv/bin/python constraint_transfer.py --split heldout --reference runs/step4-development --out runs/step4-heldout
```

Use new output directories. The [Step 4 record](experiments/level-04/README.md)
defines the restricted four-clue domain, structural split, matched controls,
and [protocol](experiments/level-04/001-frozen-transfer/README.md). All learning
is inherited; no new Step 4 training runs. Spatial relevance is engineered and
both splits share the same 16 familiar neural inputs. The outside-clue shortcut
also solves this restricted dataset, but that clue is excluded from the
implemented agent's input. Sequential puzzle solving remains a later task.

## Sources

The neural runtime is the pinned [Stonkfly implementation](https://github.com/nftechie/stonkfly/tree/78ef3e05ab0fa086032098558d893667068944a0),
adapted upstream from Doomfly, copyright © 2026 nftechie and DOOMFLY contributors.
Its [MIT license](https://github.com/nftechie/stonkfly/blob/78ef3e05ab0fa086032098558d893667068944a0/LICENSE)
is preserved in the separate checkout. [MaleCNS v1.0](https://male-cns.janelia.org/download/)
is separately downloaded data from the MaleCNS collaboration and contributors,
under CC BY 4.0; its attribution and publication citation requirements remain.

[RESEARCH.md](RESEARCH.md) preserves the historical source audit and proposed
progression toward Sudoku. Its initial research-only status describes the audit
date; this README and recorded runs describe the implemented assisted curriculum.
