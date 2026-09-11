# Independent completion audit: image-derived cue conditioning

Audited 2026-09-10, using the completed `probe/` and `train/` artifacts and
`compare_symbols.py` source SHA-256
`3eebe283252188b5285bda1474eb52d8d5f88445cd166ab2853101282b8d1c2a`.
This audit reran artifact, record, snapshot, and sensory-encoding checks. It did
not run another neural simulation.

**The declared Step 1 behavioral gate passes for experiment 005's engineered
image-to-KC interface and fixed MBON readout.** This supplies evidence to proceed
to symbol comparison under that interface. It does not turn the failed native
retinal/DNp20 experiments into successes.

## Requirement-by-requirement evidence

| Requirement | Independently checked evidence | Finding |
|---|---|---|
| Reproducible source and artifacts | All 13 probe and 30 training manifest hashes match. Both protocols' main and imported source hashes match the inspected files. The training reference hash matches the completed probe summary. | Pass |
| Fixed input transformation without labels | Reconstructed the seeded random filters, checked their hash, rerendered all ten input records, and reproduced every selected KC set from pixels. The cue encoder receives pixels, fixed filters, a fixed pool, and a fixed active count; target labels do not enter it. | Pass |
| Distinguishable, stable cue activity | Base cue ensembles overlap in only one of 16 KCs. All 256 training cue presentations produce 112 spikes exclusively in the selected 16 KCs, with zero selected-DAN spikes. Following feedback and consolidation have zero KC and MBON spikes. | Pass for this protocol |
| Label-blind fixed decoder | Untrained base raw scores are +3.5 and -1.5 Hz. Their pooled mean fixes the offset at 1 Hz; the stated deadband formula fixes the threshold at 3.5 Hz. These values match the training protocol and are not revised after reinforcement. | Pass |
| Both opposite mappings and both training orders | Recomputed targets and actions from every raw evaluation record. Both seeds, 20260911 and 20260912, pass both mappings at 8/8 correct decisions per run, with no paired timeouts. | Pass |
| Held-view performance | Training uses only the two base images, eight presentations each per arm/run. Paired evaluation scores 100% separately for base, shift, thin, and thick views. | Pass, with qualifications below |
| Advantage over controls | Paired accuracy is 100% in each run. Frozen/no-feedback accuracy is 12.5% for mapping 0 and 0% for mapping 1; inconsistent-pairing accuracy is 0%/12.5%. These satisfy the 25-point improvement gate. Each control has seven timeouts among eight decisions. | Pass |
| Correct control schedules | Every arm uses the recorded 16-trial schedule. Frozen pulses match paired pulses exactly; no-feedback pulses are absent. Inconsistent pairing supplies four reward and four aversive pulses to each cue, preserving the overall dose while preventing a consistent assignment. | Pass |
| Retained changes in existing connections | All 16 snapshots have the same 7,835 eligible edge indices. Paired snapshots change 60 edges in mapping 0 and 56 in mapping 1; inconsistent snapshots change 112. Snapshot weight-change counts and latent-state hashes match the summaries. | Pass |
| No learning without imposed feedback in this calibration | All frozen and no-feedback snapshots have zero changed edges and zero `u/w`. Their full spike-count hashes match the corresponding baseline evaluations exactly. | Pass |
| Frozen evaluation and memory erasure | Every frozen phase's before/after effective and latent memory summaries match. Each arm's eight erased evaluations reproduce its run's eight baseline full spike-count hashes exactly. All 128 erasure comparisons pass. | Pass |
| Unchanged nonplastic connections | Inspected the executed source's full-weight hash comparison after temporarily restoring the plastic subset to baseline. Every completed arm reports this check passed. | Pass as a runtime invariant; see scope below |

The raw training log contains 544 top-level records: 256 training trials and
288 evaluations. Each training record also retains its feedback and
consolidation measurements. Summary accuracy, timeout counts, ordered spike
hashes, and schedules agree with these records. The minimum paired decision
margin is **2.5 Hz beyond the 3.5 Hz threshold**.

## What the generalization evidence does and does not show

There are **32 paired evaluation decisions**, comprising eight base-image
decisions and **24 decisions on held-out image views**, across four separately
trained mapping/order states. These are not 32 independent novel stimuli or
experimental subjects.

Translation is normalized by the fixed crop/resize adapter: shifted images have
different image hashes but exactly the same KC codes as their base images.
Their success therefore checks this engineered invariance; it does not show
that the fly learned translation invariance.

Thin and thick images do change the input representation. Relative to the 16
base KCs, vertical thin/thick views share 14/13 cells; horizontal thin/thick views
share 15/15. All of these altered codes still receive the correct learned
response in both mappings and orders. This is limited robustness to the declared
image perturbations, rather than a claim about arbitrary visual generalization.

The two training orders produce matching reported responses for each mapping,
but the run does not separately duplicate each learned evaluation within the
same saved state. The controlled initial state, frozen-memory checks, and exact
erasure comparisons provide the recorded reproducibility evidence. Broader
robustness to different random encoders, tonic currents, neural noise, or long
retention intervals remains unmeasured.

## Model and evidence boundary

The adapter crops foreground pixels, resizes to 8 by 8, normalizes contrast,
applies fixed random filters, and activates the top 16 KCs from an anatomically
selected pool of 256. Retinal input and lamina bias are zero. All six MBON07/11
output cells receive a declared constant background current of 5.5 model units.
The readout is mean MBON11 rate minus mean MBON07 rate, with one global fixed
offset and threshold. These are engineered sensory and decision interfaces.

Training changes existing KC-to-MBON synapses using the pinned local rule and
supervised valence pulses delivered through DANs. No externally trained
classifier or decoder weights are present. The teaching pulse expresses the
assigned cue valence, regardless of the chosen action; this establishes
Pavlovian cue association, not reinforcement learning of an action policy.

Nonplastic preservation is checked by a full-network runtime hash assertion in
the source. Archived snapshots contain only plastic memory arrays, so this
audit cannot independently reconstruct a historical full-network state from
those snapshots alone. It verifies the assertion's implementation and the
completed result, rather than claiming an additional independent full-network
rerun.

The supported completion claim is retained image-derived cue discrimination
inside the simulation under experiment 005's explicit interface. Natural fly
vision, the original retinal-to-DNp20 pathway, symbol comparison, and Sudoku
ability are outside this Step 1 result.
