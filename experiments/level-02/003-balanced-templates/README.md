# Step 2 development: anatomically balanced template routing

This variant retains the existing plastic KC→MBON07/11 edges and local
dopamine-gated rule, with full-connectome spiking and a fixed MBON difference
readout. It replaces the interfering random sensory code with an explicitly
engineered nearest-template parser. Four base-image patches are deduplicated
without labels, sorted by pixel hash, and independently permuted for candidate
and row roles. All 16 Cartesian pairs receive identical treatment; no equality
test or class label selects neurons. The existing neurons assigned to each pair
are balanced using only their anatomical contacts to the six output neurons.

Single-pair training drives all 16 neurons in a pair's group. Two-row recall
drives eight fixed representatives from each of the two constituent groups,
four per hemisphere. This supplies the compositional sensory interface; the
synaptic valences must be learned. Equal input pooling, template recognition,
and row-order invariance are engineered, not discoveries made by the fly.

The development pilot uses all 16 single-row/candidate pairs in base rendering,
with matching pairs repeated three times per epoch to balance class exposure.
Four epochs at eta 0.00075 are fixed before reinforcement. This gives stronger
learned aversive evidence for a matching pair so it can survive pooling with a
nonmatching pair. The reversed mapping exchanges dopamine signals exactly.
It is supervised valence conditioning, not reward for a chosen action.

The decision threshold is fixed at 2 Hz, the project's original readout
deadband, rather than forcing every untrained stimulus to time out. A single
unlabelled training-image mean sets the offset before any reinforcement.
There is no per-image output correction or trained decision head.

Evaluate all 48 ordered two-distinct-symbol rows/candidates, each in four
renderings. Every two-row composition is unseen during training. All renderings
map to the same template identities, so view invariance is supplied by the
parser. Report these as repeated renderings of a 24-case unordered domain,
not independent examples of fly visual generalization.

The pilot has both mappings, one order, and erasure checks. It cannot pass the
full Step 2 gate, which additionally requires two orders, all three controls,
≥90% balanced accuracy per run, ≥85% each class/candidate/view, and ≥25 points
over every control. Development outcomes must be retained; a fixed protocol
with fresh routing/training seeds will be required after development succeeds.

## Outcome

The pilot completed both mappings. All 16 trained single-pair images were
recalled correctly in both. Unseen two-row compositions scored **79.17% / 100%**
under the two mappings. The first mapping had 40/192 timeouts and no opposite
answers; all its signed scores pointed in the correct direction but ten ordered
rows fell inside the fixed 2 Hz deadband. This is a failed adequate-performance
pilot, not a full controlled Step 2 success. Both exact-erasure checks and
nonplastic preservation checks passed. Minimum efficacy was approximately 0.24,
so saturation did not explain the remaining failures.

```sh
.venv/bin/python compare_symbols.py probe --task symbols --encoder templates --eta 0.00075 --epochs 4 --threshold-hz 2 --training-seed 20260913 --out experiments/level-02/003-balanced-templates/probe
.venv/bin/python compare_symbols.py pilot --task symbols --encoder templates --eta 0.00075 --epochs 4 --threshold-hz 2 --training-seed 20260913 --reference experiments/level-02/003-balanced-templates/probe --out experiments/level-02/003-balanced-templates/pilot
```
