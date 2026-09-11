# Development: error-contingent weakening without potentiation

Experiment 006 improves mapping 0 but destabilizes mapping 1. The source
memories are already strongly bidirectional, and incorrect three-peer inputs
activate shared features of both classes. Further opposing-compartment
potentiation can interfere with responses that were previously correct.

Change one teaching component: omit the opposite-DAN-before-cue strengthening
phase. Each incorrect or undecided judgment receives its target DAN pulse for
200 ms with learning enabled, followed by 250 ms passive relaxation. The cue
was presented for 500 ms before that pulse. The unchanged upstream local rule
therefore weakens the selected compartment's existing recently active synapses. Correct
trials remain frozen. No direct weight edits or output fitting are introduced.
Omitting that phase also removes its extra cue exposure and second dopamine
pulse, reducing time after the judgment from 1.4 seconds to 0.45 seconds.
This is a teaching-protocol intervention, not an
isolated perturbation of potentiation with every other exposure held equal.

Keep experiment 006's original 24 simultaneous KCs, current 30, output current
5.5, eta 0.00075, offset 1.625 Hz, 2 Hz deadband, eight fixed balanced epochs,
source orders/mappings, shared paired Step 2 starting memories, and all gates.
Frozen/no-feedback arms replay the exact paired events. Inconsistent events
are shuffled across the same fixed cue order, preserving teaching-event counts
and target pulse counts but relocating active windows. No-feedback allows
passive drift; erasure separately restores the inherited and untrained states.

This is a mechanistic development trial, not a promise of convergence. Report
clipping during training as well as final bounds. All held-out grids remain
reserved until the complete development gate passes. The board families alias
the same 16 neural inputs, so confirmation cannot establish neural generalization.

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --train-epochs 8 --teaching depression --out experiments/level-03/007-depression-conditioning/development
```
