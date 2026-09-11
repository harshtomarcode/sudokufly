# Development: slightly weaker output background current

Test one shared excitability change: uniform MBON current5.0 instead of5.5.
Use the original24 simultaneously driven KCs, current30,500ms frozen recall,
all saved Step2 memories, the original1.625Hz offset and2Hz deadband. No new
learning occurs. No per-neuron output coefficients or thresholds are fitted.
All development boards, mappings, orders, controls and gates remain unchanged.

The24-KC control has a spike-count plateau; staggering lowers synchrony but
does not restore reliable judgments. Moving the output membrane farther from
threshold may make existing synaptic differences matter before the next spike
resets conductance. This is a hypothesis, not a promised fix or an independently
calibrated optimum. The held-out family remains reserved.

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --mbon-current 5.0 --out experiments/level-03/005-output-current/development
```
