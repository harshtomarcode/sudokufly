# Development: three fixed rounds of label-blind common weakening

Experiment 008 passes mapping 0 but leaves 11 of 12 invalid inputs in mapping 1
just below the fixed rejection threshold. Their MBON11 rate remains 14 Hz;
MBON07 still produces enough spikes to leave only 1.375–1.875 Hz after the
unchanged offset. Test whether one more common weakening round crosses the
next output spike-count threshold.

Change only calibration rounds from two to three. The code, original source
memories/controls, group order, eight KCs per group, both simultaneous DAN
pulses, currents, durations, 24-cell board input, decoder, numerical gates,
arm-specific stage erasure, and full erasure remain exactly as in 008. No board,
label, score, or target mapping chooses calibration events. Every arm receives
48 fixed events; evaluate only the final three-round state. Report clipping
and any lost valid-candidate responses, not just improvements on rejects.

This dose was chosen from earlier development evidence. It is not an untouched
zero-shot benchmark, a claim of new board-labelled learning, or a relaxation of
008's failed gate. If all development conditions pass, commit the final states
and source before evaluating the reserved 192-grid family. The two families
still alias the same 16 neural representations.

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --calibration-epochs 3 --teaching depression --out experiments/level-03/009-three-round-calibration/development
# Only after development passes:
.venv/bin/python one_blank.py --split heldout --per-pair 8 --timing simultaneous --teaching depression --conditioning-source experiments/level-03/009-three-round-calibration/development --out experiments/level-03/009-three-round-calibration/heldout
```

## Outcome: both mappings fail

Both source orders give paired balanced accuracy 91.67% / 58.33% for mappings
0 / 1. Accept recall, precision and scan completion remain 100%, but rejection
recall is only 83.33% / 16.67%. Calibrated original controls score 20.83% / 25%.
The unchanged class/subgroup gates correctly fail. In mapping 0, two candidate-3
invalid inputs now have MBON07 and MBON11 both at 11 Hz, producing -1.625 Hz
and a timeout: extra weakening damaged their prior negative decision.

The first two calibration rounds reproduce 008's records exactly. The third
round reaches the latent lower clamp at some phase endpoints. Both erasures
and preservation checks pass. Runtime was 208.30 seconds. The held-out family
remains reserved; this dose does not complete Step 3.
