# Experiment 004: direct neural association calibration

Date: 2026-09-10. **The declared internal calibration gate passed in all four
mapping/order combinations. Visual Level 1 remains incomplete.**

The simulation can store two opposite cue–valence associations through changes
to its existing KC→MBON synapses. This experiment supplies synthetic input
directly to Kenyon cells and uses an engineered fixed MBON comparator. It does
not establish recognition of stripe images, reinforcement of a chosen action,
Sudoku ability, or an advantage of the connectome over simpler networks.

## What changed

The full original `MemoryBrain` graph and its 7,835 eligible KC→MBON07/11
connections are retained. The pinned learning equation, initial weights,
0.1-ms neural timestep, and neuron parameters are unchanged. There are no added
graph connections and no trained external readout weights.

- **Input:** two disjoint groups of 16 KCs, eight per hemisphere in each group.
  Every selected cell has existing inputs to both memory-output compartments.
  Selection uses anatomical contact counts only, before reinforcement.
- **Sensory background:** retinal input and lamina bias are zero. The visual
  adapter is not used.
- **Output background:** a constant current of 5 model units is applied equally
  to the six MBON07/11 cells. It is identical for every cue, mapping, and arm.
  This is an explicit artificial excitability calibration, not measured biology.
- **Readout:** mean MBON11 firing rate minus mean MBON07 firing rate, minus one
  global untrained offset of 8.5 Hz. Values ≥+5 Hz mean accept/reward; values
  ≤−5 Hz mean reject/aversive; intermediate values are timeouts. The coefficients,
  threshold, and offset are frozen before any reinforced trial. The offset
  uses both unlabelled baseline responses and contains no cue-specific lookup.
- **Teaching:** cue A/B is paired with its assigned reward or aversive dopamine
  population regardless of the decoded action. This is Pavlovian conditioning.
  Correctness-based feedback would require an additional action-learning test.

Selection ranks KCs that contact both compartments, within each hemisphere,
by descending minimum contact count, descending total count, then numerical
body ID. Alternating the first 16 ranks assigns eight cells to each cue.

| Anatomical property | Cue A | Cue B |
|---|---:|---:|
| Stimulated KCs | 16 | 16 |
| Existing eligible output connections | 58 | 58 |
| Contacts onto MBON07 | 287 | 277 |
| Contacts onto MBON11 | 252 | 253 |
| Output cells reached | 6/6 | 6/6 |

## Untrained calibration came first

The first [probe](probe/summary.json), preserved with its original source in
commit `0bb4f51`, activated the intended KCs but elicited no MBON spikes. Neither
learning nor a training run occurred under that configuration.

The second [probe with output background current](probe-tonic5/summary.json)
elicited output spikes while preserving clean input separation. Each 500-ms
cue produced exactly 112 spikes in its own 16 KCs, zero in the other group,
and zero in other KCs. The two raw comparator values were both 8.5 Hz. Silent
input, cue offset, and the following interval produced no KC or MBON spikes;
the selected dopamine cells were also silent throughout this unreinforced probe.

Thus one label-blind offset makes both untrained cue scores zero. The zero-current
and 5-current probes are both retained; no parameters were selected using trained
accuracy. Probe actions were calculated before centering and are not the final
calibrated baseline decisions.

## Learning protocol

Each trial starts from fresh electrical state and activity traces, retaining
learned weights and latent `u/w` memory:

1. **500 ms cue:** 30 units of current into the cue's 16 KCs. Weights remain
   frozen while the learning rule's activity traces accumulate.
2. **200 ms feedback:** remove imposed KC stimulation; apply 20 units to the
   assigned PAM11 reward or PPL101 aversive cells. Enable local plasticity.
3. **250 ms consolidation:** no imposed cue or feedback. Disable the associative
   drive while permitting passive `u→w` relaxation. This differs from freezing
   all weight dynamics.

Both opposite assignments are tested with each of two fixed balanced eight-trial
orders. Every run starts from original weights. Each cue receives four pairings.
The fixed response is evaluated with learning and feedback disabled.

The frozen arm receives the exact paired pulses with memory frozen. The
no-feedback arm receives no imposed dopamine pulse but uses the same learning
windows. The inconsistent arm receives the same overall four reward/four aversive
pulses, arranged so each cue receives two of each. It cannot accidentally form
a clean reversed assignment. Complete schedules are in the training protocol.

## Results

| Condition | Order 0, mapping 0 | Order 0, mapping 1 | Order 1, mapping 0 | Order 1, mapping 1 |
|---|---:|---:|---:|---:|
| Paired conditioning | 100% | 100% | 100% | 100% |
| Frozen weights | 0% | 0% | 0% | 0% |
| No external feedback | 0% | 0% | 0% | 0% |
| Inconsistent pairing | 0% | 0% | 0% | 0% |
| Erased memory | 0% | 0% | 0% | 0% |

**All control responses are timeouts, not incorrect choices or chance-level
classification.** There are eight distinct trained cue decisions across four
trained states. Each is repeated to verify determinism, producing 16 matching
records; those repeats are not independent experimental subjects.

| Assignment | Learned A score | Learned B score | Decision |
|---|---:|---:|---|
| A reward / B aversive | +5.5 Hz | −8.0 Hz | Accept A, reject B |
| A aversive / B reward | −10.0 Hz | +5.5 Hz | Reject A, accept B |

Both orders produce the same displayed scores. Frozen and no-feedback scores
are zero; inconsistent pairing produces −2.5 Hz for A and −1 Hz for B.

Each paired run changes exactly **58 connections**: the rewarded cue's 32
KC→MBON07 connections and the aversive cue's 26 KC→MBON11 connections. Their
weighted efficacies fall to approximately **0.660 of baseline**, a 34% decrease.
The other compartment's inputs from each cue remain unchanged, as do inputs
from unstimulated KCs. No efficacy reaches a bound. Inconsistent pairing changes
all 116 eligible connections belonging to the two cues; frozen and no-feedback
training change zero.

Erasure restores the original complete spike-count hashes, not just the decoded
action. All evaluations preserve effective and latent memory, repeated responses
match exactly, and every nonplastic connection remains unchanged. Sixteen final
memory-only snapshots retain edge indices, effective weights, and `u/w`.

## Interpretation and limits

This is a positive result for local, retained association learning in the
simulator. The earlier visual failures did not establish that its plasticity
rule was incapable of storing associations. Here the input groups are distinct,
reinforcement reaches their connections, and learning occurs in a defined
pairing window.

The positive score is only **0.5 Hz above the fixed decision threshold**. No
claim of tolerance to input-current perturbations, altered cue ensembles, or
other neural states is justified by this run. The result uses direct stimulation,
constant output background current, and a changed output interface; its
accuracy is not directly comparable to the visual DNp20 assay. Multiple design
changes were introduced together, so this experiment does not isolate their
individual necessity. Order replication is limited to two deterministic orders.

Visual Level 1 still requires a validated route from images to distinguishable
memory activity and an explicit visual-task protocol. The next work remains at
Level 1; this calibration is not permission to advance to symbol comparison.

## Reproduction and audit

Use the repository's existing environment and pinned upstream checkout. From
this experiment's committed source version:

```sh
.venv/bin/python calibrate_step1.py probe --mbon-current 5 --out runs/direct-probe
.venv/bin/python calibrate_step1.py train --mbon-current 5 --reference runs/direct-probe --out runs/direct-train8
```

Training refuses a mismatched or altered probe, and output directories must
not already exist. The archived zero-current probe uses the original source
at `0bb4f51`; its exact source hash differs from the completed runner.

The [training protocol](train8/protocol.json) records the source hashes, input
identities, model settings, decoder, and gates before training. The
[summary](train8/summary.json) hashes its artifacts; [trials](train8/trials.jsonl)
retain 10-ms neural counts and before/after memory summaries. The 528 recorded
phases include 128 training trials and 144 frozen evaluation presentations.
Scores outside cue/evaluation phases are diagnostic calculations, not decisions
used to choose reinforcement.

Independent [scientific](scientific-audit.md) and
[artifact](artifact-audit.md) audits accompany the record.
