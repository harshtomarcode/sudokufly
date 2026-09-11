# Step 2 development: bidirectional local teaching

Experiment 003 learned every atomic pair but produced weak negative evidence
when one matching and one nonmatching pair were pooled. This variant keeps
the same template parser, anatomy-only KC partition, currents, eta, epochs,
global unlabelled offset, and 2 Hz decision deadband. It changes teaching
timing while retaining the upstream local plasticity rule unchanged.

Each trial now has two halves:

1. Present the image for 500 ms with weights frozen, then apply the target DAN
   pulse for 200 ms with learning, followed by 250 ms consolidation. Recent KC
   activity followed by dopamine depresses the corresponding compartment.
2. Reset electrical state and traces while retaining memory. Apply the opposite
   compartment's DAN pulse for 200 ms with frozen weights, then present the same
   image for 500 ms with learning, followed by 250 ms consolidation. Recent
   dopamine activity followed by KC activity potentiates that compartment.

The existing rule supplies both signs of change; no new weight-learning rule
or external decision head is fitted. One pulse reaches each compartment on
every trial. The supervised label selects temporal order, not total pulse dose.
This is an engineered teaching protocol, not a claim about natural fly training.

All sensory parsing and task limits from experiment 003 apply. The pilot tests
both answer mappings with order 20260913. It cannot pass the full gate without
the subsequent fresh fixed-protocol replication and controls. The same ≥90%
per-run / ≥85% class-candidate-view / ≥25-point control gates remain fixed.

```sh
.venv/bin/python compare_symbols.py probe --task symbols --encoder templates --teaching bidirectional --eta 0.00075 --epochs 4 --threshold-hz 2 --training-seed 20260913 --out experiments/level-02/004-bidirectional-pilot/probe
.venv/bin/python compare_symbols.py pilot --task symbols --encoder templates --teaching bidirectional --eta 0.00075 --epochs 4 --threshold-hz 2 --training-seed 20260913 --reference experiments/level-02/004-bidirectional-pilot/probe --out experiments/level-02/004-bidirectional-pilot/pilot
```

## Outcome: accuracy passed; full controls still required

Both mappings scored 100% on all 16 trained atomic pairs and all 24 distinct
unseen two-row compositions (192 rendered/ordered presentations per mapping).
There were no timeouts. Both erasure checks restored all baseline spike-count
hashes exactly; nonplastic weights were unchanged. Exactly 909 existing edges
changed per mapping, including both depression and potentiation. The first
mapping's weakest decision cleared the unchanged 2 Hz deadband by 3.125 Hz.

The pilot is not a completed Step 2 gate: it uses one training order and lacks
the three full training controls. The next experiment freezes this method and
uses fresh routing and training seeds with all controls. No tuning on that
replication's outcomes is permitted while calling it a confirmation.
The subsequent [controlled replication](../005-controlled-replication/README.md)
completed and passed all gates.
