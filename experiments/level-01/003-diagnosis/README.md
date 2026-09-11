# Experiment 003: why Level 1 is unreliable

Date: 2026-09-10. **Step 1 remains incomplete.** These are post-hoc diagnostics
of experiments 001/002, not independent confirmation or a new progression gate.
The original runner, fixed decoder, and earlier artifacts are preserved.

The model is changing and retaining synaptic weights. The failure is that those
changes do not reliably encode the requested cue-to-action association. The
original cue-active memory connections lack a direct reward-modulation route,
the largest measured changes occur outside the decision interval, initial KC spike
count summaries overlap strongly, and the one successful saved classifier
is sensitive to small input and initial-state changes. A delayed activity burst
exists even with constant input and frozen weights: the blank transition is
not its necessary cause.

## 1. Initial memory-neuron count summaries overlap strongly

At the start of training, both patterns activate the same four of 4,064 Kenyon
cells (KCs). Their body IDs and 500-ms spike counts are:

| Cue | 18540 | 21778 | 44069 | 520206 | Total |
|---|---:|---:|---:|---:|---:|
| Vertical | 8 | 7 | 1 | 1 | 17 |
| Horizontal | 7 | 7 | 1 | 1 | 16 |

The 10-ms timing patterns differ, so this is not proof that all cue information
is absent. However, these are nearly identical population count vectors at the
neurons whose outgoing connections learn. Separation in the time-dependent
eligibility signal remains unquantified; these counts alone do not establish
its absence. Endogenous dopamine also differs substantially: 16 versus 97
initial PPL spikes. The interface needs validation at the actual learning
signal, beyond merely showing that the two images produce different spikes.

### The initial baseline representation has no direct reward-plasticity route

The four active KCs have only **five** eligible outgoing connections in the
original circuit. All five target MBON11; none target MBON07. The original
compartment rule assigns PAM11 reward gain zero to these MBON11 connections.
Thus the reward pulse cannot directly modify the initial cue-active memory
connections through that rule. The phase assay corroborates this: vertical
reward produces 270 PAM spikes yet the same weight movements as no pulse.

Expansion raises those four cells' eligible outputs to 65, including 18 with
nonzero PAM modulation gain. This opens a missing local route, but does not
validate the added modulation gains or solve the other problems. Later bursts
recruit other KCs, so the initial baseline bottleneck does not mean every reward
pulse throughout training is ineffective. See [the exact circuit table](circuit-audit.md).

## 2. Large changes happen without an external teaching signal

The phase assay starts each trial with baseline weights and fresh electrical
state. Observation lasts 500 ms, feedback 200 ms, and the bright blank 250 ms.
Learning is enabled throughout, as in the original protocol.

For the expanded circuit and horizontal cue, **with no imposed dopamine pulse**:

| Phase | KC spikes | Active KCs | Weight movement, L1 |
|---|---:|---:|---:|
| Observe cue | 16 | 4 | 19.45 |
| Continue cue without feedback | 5 | 2 | 14.75 |
| Bright blank | 3,469 | 1,380 | 2,430.04 |

After this single unreinforced sequence, 10,707 connections have changed. The
original smaller circuit shows the same pattern: 2,728 spikes during its blank
interval and 2,602 changed connections. Across both scopes and all three
horizontal feedback conditions, the blank contributes **98.57–98.93% of summed
per-phase endpoint L1 movements**. This statistic is not the fraction of final
memory causally attributable to a phase, nor the integral of all updates.

The rule observes endogenous dopamine activity too: the initial horizontal
observation already produces 97 PPL spikes, without external feedback. KC
activity after that dopamine activity can engage the potentiating side of the
temporal rule. Thus "no reward pulse" does not mean "no learning signal."

### The blank does not cause the burst

A matched intervention continues the cue instead of switching to blank. The
first 700 ms are identical within each pair, and no external feedback is given.
The final 250 ms show:

| Horizontal sequence, 700–950 ms | KC spikes | Active KCs | Weight movement, L1 |
|---|---:|---:|---:|
| Normal plasticity, switch to blank | 3,469 | 1,380 | 2,430.04 |
| Normal plasticity, keep the cue | 3,673 | 1,462 | 2,474.23 |
| All weights frozen throughout, switch to blank | 2,744 | 1,404 | 0 |
| All weights frozen throughout, keep the cue | 2,652 | 1,363 | 0 |

Vertical produces eight spikes in the final interval in all four conditions.
Thus a delayed, cue-dependent response exists without a stimulus transition,
external feedback, or plasticity. Changing the blank alone cannot remove its
underlying cause. Plasticity changes the late response, but does not create it.

This corrects the initial hypothesis suggested by phase measurements. The
decision samples the first 500 ms; training remains active through a much
stronger response at 700–950 ms. Electrical state resets before the next trial,
while the resulting weights persist. The observation window therefore omits
much of this delayed response while the learning window includes it. That is a
measured timing mismatch; whether extending observation fixes classification
has not been tested. The exact recurrent pathway causing the burst remains
unresolved.

### Training order and feedback controls

The first pilots paired mapping 0 with order 0 and mapping 1 with order 1.
The diagnostic crosses both mappings with both original eight-trial orders:

| Order | Target mapping | Original training | No external feedback | Freeze blank interval |
|---|---|---:|---:|---:|
| 0 | Vertical accept / horizontal reject | 50% | 50% | 50% |
| 0 | Vertical reject / horizontal accept | 50% | 50% | 50% |
| 1 | Vertical accept / horizontal reject | 0% | 50% | 50% |
| 1 | Vertical reject / horizontal accept | 100% | 50% | 50% |

Each cell is one deterministic two-cue evaluation, not a statistical accuracy
estimate. The two original conditions reproduce their previous results exactly.
The successful mapping fails when the order changes. Mapping 0's 0% condition
times out on vertical and incorrectly accepts horizontal.

Without external feedback, orders 0/1 still change **14,027 / 14,677** edges.
Both label assignments then produce identical complete spike hashes within
each order, as they should: labels no longer influence the simulated training.
External feedback is not irrelevant—it is needed for the original successful
case—but extensive weight change alone is not evidence of task learning.

Freezing the blank interval yields 50% in every crossed condition. It does not
repair the task. This intervention freezes both associative changes and passive
`u→w` consolidation, so it is not a pure test of disabling the learning-rule
drive. Small earlier changes can also alter activity in subsequent trials.

## 3. The earlier successful result does not survive small changes

Frozen evaluation of experiment 002's successful mapping-1 memory gives:

| Input/state condition | Vertical difference, Hz | Horizontal difference, Hz | Accuracy |
|---|---:|---:|---:|
| Exact original conditions | −4 | +8 | 100% |
| Shift image right by 1 pixel | +2 | +10 | 50% |
| Shift image down by 4 pixels | +2 | +6 | 50% |
| Show blank for 500 ms before cue | +4 | +2 | 50% |

The target is vertical→reject, horizontal→accept; positive differences mean
accept. These stress tests were not part of the original declared gate. They
show that its mapping-1 success is specific to the original input/state assay.

Sensitivity exists even before learning: moving the untrained vertical image
one pixel changes its KC count from 17 to 2,917. This implicates the sensory and
recurrent dynamics, beyond the learned weights alone. The retinal adapter uses
point sampling and a nonlinear current transform; that source observation does
not isolate which component causes this sensitivity.

## 4. More plastic connections introduced consequential assumptions

Both pilots already simulated all 25.6 million graph connections. Expansion
increased the number allowed to learn from 7,835 to 34,249.

Seventeen added MBON targets have at most two contacts from the selected
dopamine cells. Normalizing these contacts still gives each target total
modulation gain one. These targets receive 11,991 plastic connections; their
changed weights account for 24.39% of mapping-1 absolute weight change.

Restoring selected weight groups to baseline, while preserving all other
learned weights, produces the following frozen vertical readouts:

| Restored group | Vertical difference, Hz | Original reject retained? |
|---|---:|---|
| None | −4 | Yes |
| MBON05 inputs | −2 | Yes, at threshold |
| MBON11 inputs | 0 | No: timeout |
| MBON03 inputs | −4 | Yes |
| Targets with at most two selected-DAN contacts | +6 | No: accept |
| All original MBON07/11 targets | +2 | No: accept |
| All added targets | +8 | No: accept |

Horizontal remains accept in each case. Restoring the weakly supported group
removes this particular saved success. This is a group-level intervention; it
does not identify which individual changes are necessary, validate the assumed
gains, or prove an isolated neural pathway mechanism.

The heavily changed MBONs participate in inhibitory feedback through APL to
KCs, while lacking direct or two-hop modeled spike-transmitting paths to the
decoder. This is a plausible route for broad changes in recurrent activity, not a demonstrated
single cause. Opposite target mappings also produce highly correlated efficacy
changes: 0.9253 across all expanded edges, 0.9006 across the changed-edge union.
See [the static circuit audit](circuit-audit.md) for calculations and limits.

## 5. The learning rule and decoder need separate validation

The active Python rule does run; weights are preserved across trials, frozen
evaluation really freezes them, and erasure restores baseline behavior. No
reset or disabled-learning bug was found.

Its update is `q = eta * (K * filtered_D − D * filtered_K)`, followed by slow
latent memory and effective-weight dynamics. Reward and aversive populations
enter the same algebraic rule; their meanings depend on circuit targets and
timing. There is no explicit eligibility for the selected motor action. A
correctness pulse therefore does not mathematically guarantee movement toward
the desired action.

Equal KC/DAN trace filters cancel updates for exactly proportional activity.
The cited physiological model instead permits asymmetric traces, fits their
aggregate pairing effects, and subtracts baseline activity. Delayed feedback
breaks proportionality in this pilot, so
cancellation is a model limitation, not an explanation for zero total learning.

The DNp20 spike-difference decoder is also an engineered interface. Physiology
identifies DNp20/DNOVS1 as a neuron with graded responses in the studied
preparation. Neither its artificial spike dynamics nor its arbitrary
accept/reject labels establish an appropriate learned-choice channel. See the
[primary-source model audit](model-audit.md) for citations and code references.

## What to repair next, within Step 1

1. Measure the full cue response over time, then establish distinct, stable
   responses at the plastic KC inputs across modest image shifts and a consistent
   pre-cue state. Align decision and learning windows using that measurement.
   If using directly
   injected KC patterns for circuit calibration, label that as a synthetic
   input diagnostic; it would not complete visual cue learning.
2. Separate cue/feedback eligibility from late and intertrial activity.
   Compare with no external feedback and frozen controls. Distinguish disabling
   the associative update from freezing passive memory consolidation.
3. Verify that each selected dopamine population and memory compartment can
   move the fixed choice signal in a predictable direction, then calibrate
   baseline and timing assumptions as separate variants.
4. Cross both label mappings with the same training orders. Predeclare new
   orders and image variants for confirmation after choosing a protocol.

Increasing connection count or training duration again would mix these issues
together. None of these diagnostics establishes Sudoku ability or a limitation
of real fruit flies.

## Reproduction and record

`diagnose_step1.py` uses the existing environment and pinned upstream data.
The original diagnostic source is preserved in commit `e8df3db`; it generated
`phases`, `snapshots`, and `training`. A subsequent additive `transition` suite
isolates the blank transition. Every suite records its source hash, runner hash,
upstream commit, verified graph, 10-ms measurements, and evaluation spike hashes.
The training suite retains trial choices and pulses plus full final evaluation
measurements; it does not retain per-phase measurements for every training trial.

```sh
.venv/bin/python diagnose_step1.py phases --out runs/diagnosis-reproduction
.venv/bin/python diagnose_step1.py snapshots --out runs/diagnosis-reproduction
.venv/bin/python diagnose_step1.py training --out runs/diagnosis-reproduction
.venv/bin/python diagnose_step1.py transition --out runs/diagnosis-reproduction
```

Run serially. Existing result files are refused. The current source preserves
the behavior of the first three suites; exact original source hashes resolve
through `e8df3db`. Audits and final checks accompany the raw JSON/JSONL records.

At this experiment's committed source version, recheck the retained record with:

```sh
.venv/bin/python experiments/level-01/003-diagnosis/audit.py
```

The audit checks record counts, bins and neural totals, fixed decoder arithmetic,
frozen weights, matched intervention prehistory, exact original response hashes,
crossed schedules, label independence without feedback, source versions, and all
22 original artifact hashes. It writes [summary.json](summary.json), including
the training comparison and hashes of this diagnosis's artifacts. These are
consistency checks, not additional experimental replications.
