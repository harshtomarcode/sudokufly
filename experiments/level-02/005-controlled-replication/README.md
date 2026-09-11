# Step 2: fixed-protocol controlled replication

**Passed.** All four fresh mapping/order conditions met every predeclared gate.
Executed source and the untrained calibration were committed as `5aa3db1`
before reinforcement. Later source edits only clarify the adapter docstrings.

| Training order | Mapping | Learned | Frozen | No feedback | Inconsistent timing |
| --- | --- | --- | --- | --- | --- |
| 20260919 | 0 | 100% | 8.33% | 8.33% | 8.33% |
| 20260919 | 1 | 100% | 0% | 0% | 0% |
| 20260920 | 0 | 100% | 8.33% | 8.33% | 8.33% |
| 20260920 | 1 | 100% | 0% | 0% | 0% |

Every learned state answers all 24 distinct unseen compositions correctly,
with no timeouts. Every class, candidate, rendering, and match position scores
100%. The weakest learned decision clears the fixed threshold by 3.125 Hz.
All 16 trained atomic pairs are also recalled correctly in every learned state.
These are four trained states over one small exhaustive task domain, not
hundreds of independent generalization trials.

Paired teaching changes exactly 909 existing synapses per run, with both
strengthening and weakening. Efficacies remain approximately 0.256–1.830 times
baseline, away from either bound. Frozen and no-feedback arms change no memory.
Inconsistent timing also changes 909 synapses, but does not acquire the task;
its changes are small common potentiation. Thus the learned sign pattern,
not merely the presence of weight changes, carries the comparison responses.

All 16 erasure interventions recover baseline full spike-count hashes exactly
for 24 measured neural inputs each. The runner also verifies the full weight
array is unchanged outside the permitted plastic edges. Snapshots retain the
effective weights and latent `u/w` states. See [the independent audit](audit.md).

The suite records 1,536 training trials and 7,168 frozen evaluation records:
1,120 actual neural evaluations and 6,048 explicitly linked input aliases.
The neural run completed in 412.35 seconds. All raw data, snapshots, input
manifests, protocols, and artifact hashes are in `probe/` and `train/`.

## Protocol fixed before reinforcement

This protocol is recorded before fresh-seed reinforcement. The learning and
representation choices were developed in experiments 001–004; their failures
and pilot results remain in Git. This is a replication within the same small
exhaustive symbol domain, not an untouched task-distribution test.

Freeze experiment 004's bidirectional local teaching, base-image templates,
anatomy-only partition, 16 active KCs, 500/200/250 ms windows, KC current 30,
uniform MBON current 5.5, eta 0.00075, four epochs, and 2 Hz deadband. Select the
offset only from unlabelled untrained single-pair responses. Use fresh encoder
seed 20260917 and fresh training orders 20260919 and 20260920, both opposite
valence mappings, and paired/frozen/no-feedback/inconsistent arms from baseline.
Do not tune this protocol using the replication's outcomes.

All 16 atomic single-row/candidate pairs are trained in base rendering. Each
matching pair appears three times per epoch and each nonmatching pair once,
giving 96 trials per arm. Every trial supplies one pulse to each compartment;
the supervised valence determines which is before versus after the cue.
Inconsistent timing assignments are exactly balanced within each image.

Test all 24 unordered two-row/candidate compositions absent from training,
represented as 48 ordered rows/candidates in four renderings. The template
parser and row pooling supply view/order invariance, yielding 24 distinct neural
inputs. Each distinct input is simulated from reset once per frozen evaluation;
the other records explicitly identify their measured-input aliases. Nothing is
reused across trained states, arms, mappings, or erasure. Before this change,
experiment 004 independently simulated 1184 evaluation presentations: all 1008
repeats matched the full spike-count hash of their identical input/state.

The fixed gate requires every mapping/order to reach ≥90% balanced accuracy,
≥85% for each class, candidate, and view, and ≥25 percentage points above
each of the three controls. Exact erasure and preservation of all nonplastic
weights are mandatory. Record match-position accuracy, decision margins, full
spike hashes, and effective/latent memory snapshots.

The claim is internal associative learning of familiar-symbol comparison
under an engineered image parser and sensory composition interface. It is not
learned fly vision, abstract equality, or Sudoku solving. The graph and local
plasticity rule remain the pinned upstream implementation.

```sh
.venv/bin/python compare_symbols.py probe --task symbols --encoder templates --teaching bidirectional --eta 0.00075 --epochs 4 --threshold-hz 2 --encoder-seed 20260917 --training-seed 20260919 --out experiments/level-02/005-controlled-replication/probe
.venv/bin/python compare_symbols.py train --task symbols --encoder templates --teaching bidirectional --eta 0.00075 --epochs 4 --threshold-hz 2 --encoder-seed 20260917 --training-seed 20260919 --reference experiments/level-02/005-controlled-replication/probe --out experiments/level-02/005-controlled-replication/train
```
