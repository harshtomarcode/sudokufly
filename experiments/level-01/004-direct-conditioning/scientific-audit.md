# Scientific audit: direct conditioning

The saved `train8` results support **controlled cue-to-valence association
learning inside the simulated KC-to-MBON connections** under the declared
direct-stimulation protocol. They pass this calibration's gate. They do not
pass visual Level 1 or establish Sudoku learning.

This review independently checked the runner and existing artifacts. It did
not rerun neural simulations. The review covered all 528 raw phase records,
all 16 memory snapshots, the 19 training artifact hashes, the two reference
probe artifact hashes, and the reference/source hash bindings. Decoder rates,
scores, actions, and correctness were recomputed from logged 10-ms output-cell
counts. Snapshot changes were independently interpreted using the static graph
and neuron annotations rather than trusting the summary's compartment labels.

## Pairing, input, and decoder checks

Each cue stimulates a fixed, distinct ensemble of 16 KCs, with anatomical
connections to both selected output compartments. The ensemble IDs match the
graph. Both mappings are crossed with the same two cue orders. Reward versus
aversive stimulation follows the assigned cue valence, independently of the
decoded action: this is Pavlovian conditioning, not correctness-based
reinforcement learning.

The readout is always mean MBON11 firing rate minus mean MBON07 firing rate,
minus one global 8.5-Hz offset, with fixed thresholds of +5 and -5 Hz. The
offset reproduces the pooled, untrained probe response. The reference probe
performs no plasticity, and its source and relevant parameters match training.
Targets enter correctness scoring after the neural response is measured; they
do not enter the evaluation stimulus or decoder. No trained output layer or
cue-specific readout lookup was found.

Cue presentation freezes weights while accumulating eligibility traces.
Feedback removes imposed KC stimulation and enables the local rule. Subsequent
consolidation disables the associative drive while allowing passive memory
relaxation. The saved flags agree with these semantics. All 128 feedback
periods contain zero KC spikes, consistent with learning from retained KC
traces. Reward pulses produce 270 selected reward-neuron spikes and zero
selected aversive-neuron spikes; aversive pulses produce zero and 36,
respectively. No-feedback periods produce neither.

## Retained response and mechanism

Both training orders produce these frozen evaluation scores:

| Assigned association | Cue A, Hz | Cue B, Hz | Correct distinct cue conditions |
|---|---:|---:|---:|
| A reward, B aversive | +5.5 | -8.0 | 2/2 per order |
| A aversive, B reward | -10.0 | +5.5 | 2/2 per order |

There are **eight distinct mapping/order/cue conditions**, all correct. Each
is evaluated twice with identical complete spike-count hashes; the resulting
16 logged paired evaluation rows are not 16 independent observations.

Each paired run changes exactly 58 connections. For each cue, the weighted
efficacy of its paired compartment falls to 0.659785–0.660275 of baseline,
approximately 34% depression. Its other compartment remains exactly at
baseline. All plastic connections from unstimulated KCs remain unchanged.
Thus the mechanism gate reflects actual target-selective depression, not
merely greater potentiation elsewhere. No final efficacy reaches either bound.

All evaluation periods freeze weights and both memory variables; raw before/
after memory records agree. Electrical state and eligibility traces are reset
before evaluation, so the retained decision difference is not simply residual
activity from the dopamine pulse. Erasing memory restores the complete
baseline spike-count hashes in every arm. The runner also checks the full
weight-array hash after temporarily restoring plastic edges, detecting changes
to nonplastic connections; all recorded checks passed. The saved snapshots
permit independent checking of plastic edges, not reconstruction of the full
electrical state.

## Controls and limits

Frozen and no-feedback controls retain baseline memory and responses exactly.
The inconsistent-pairing control gives each cue two reward and two aversive
pulses, preserving cue order and total pulse dose. It depresses both
compartments, changing 116 edges, without selective classification. Across all
three controls, every evaluated cue times out within the decoder deadband.
Their scored accuracy is 0% because of abstention; this is **not a chance-level
classification result**. No-feedback and inconsistent memories also agree
across mappings within an order, as expected when assigned labels do not
change their training inputs.

The result depends on engineered direct KC cues, explicit learning windows,
electrical resets, and a constant background current of 5 model units to all
six selected MBONs. The anatomical graph and internal learning rule remain in
use, but these interventions simplify the task substantially. The fixed MBON
comparator is an experimental readout, not a demonstrated natural motor policy.

Reward responses sit at +5.5 Hz, only 0.5 Hz beyond the acceptance threshold.
That narrow margin limits claims of robustness. These deterministic runs use
two selected ensembles and two training orders; they do not measure
generalization to new ensembles, noisy inputs, longer retention intervals,
visual stimuli, or other stimulation strengths. The successful reversal is
between separate baseline-start runs, not reversal of an already conditioned
memory. The justified conclusion is that this internal plasticity mechanism
can store and express the intended association in this calibrated assay.
