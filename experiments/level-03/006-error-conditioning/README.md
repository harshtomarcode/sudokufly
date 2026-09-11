# Development: error-contingent internal synaptic conditioning

The five transfer variants fail the full judgment gate. Now teach Step3 directly,
without changing the fixed pixel encoder, original24 simultaneous KC inputs,
KC current30, MBON current5.5, offset1.625Hz or2Hz deadband. The unchanged local
rule and original7,835plastic edges remain the only learning mechanism.

Each of the four source order/mapping conditions starts from its saved paired
Step2 memory. All four arms within a condition start from that SAME W/u/w.
Present16 unique neural inputs derived from development board images. Each of
8 fixed epochs has24trials: each of4accept inputs appears3times and each of
12reject inputs once; independently shuffle using source seed+1000+100*epoch.
Reset electrical state and traces between trials while preserving memory.

The paired arm first judges the image with frozen weights. Only an incorrect or
undecided judgment triggers the existing bidirectional teaching sequence:
cue500ms then target DAN200ms learning,250ms passive; reset electrical state;
opposite DAN200ms frozen, same cue500ms learning,250ms passive. Both DAN pulses
use current20. A correct trial ends after its frozen500ms judgment. This is
supervised error-contingent conditioning, not an externally trained policy.

Frozen and no-feedback controls replay the paired arm's exact teaching events.
The inconsistent control permutes ALL192events (including no-teaching events)
across the identical cue schedule. This preserves total event and target-timing
counts but changes which inputs and trials receive teaching; it is not a control
with the same active windows. Reject an unchanged permutation. All controls
retain the same total cue/phase counts. No-feedback allows passive drift of
inherited memory; frozen must remain identical to inherited memory.

All judgment, subgroup, precision, completion and25percentage-point control
advantage gates remain. At this operating point inherited balanced accuracy
is62.5%/50%, so that advantage remains feasible. Eight epochs are fixed in
advance; no early stopping or selected intermediate checkpoint. Log every
judgment, teaching event, phase, memory change and final snapshot. Stage erasure
must restore inherited W/u/w and responses exactly; full erasure must restore
untrained responses and preserve all nonplastic edges.

The structural held-out family remains reserved. If development passes, freeze
code/parameters/memories and render all192held-outgrids. Both families collapse
to the SAME16 neural representations, now explicitly used in training: this
confirmation tests board rendering/coverage, not novel neural representations.

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --train-epochs 8 --out experiments/level-03/006-error-conditioning/development
# Only after all development gates pass and the source is frozen:
.venv/bin/python one_blank.py --split heldout --per-pair 8 --timing simultaneous --conditioning-source experiments/level-03/006-error-conditioning/development --out experiments/level-03/006-error-conditioning/heldout
```
