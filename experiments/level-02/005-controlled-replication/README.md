# Step 2: fixed-protocol controlled replication

This protocol is recorded before fresh-seed reinforcement. The learning and
representation choices were developed in experiments001–004; their failures
and pilot results remain in Git. This is a replication within the same small
exhaustive symbol domain, not an untouched task-distribution test.

Freeze experiment004's bidirectional local teaching, base-image templates,
anatomy-only partition,16 active KCs,500/200/250ms windows, KC current30,
uniform MBON current5.5, eta0.00075, four epochs, and2Hz deadband. Select the
offset only from unlabelled untrained single-pair responses. Use fresh encoder
seed20260917 and fresh training orders20260919 and20260920, both opposite
valence mappings, and paired/frozen/no-feedback/inconsistent arms from baseline.
Do not tune this protocol using the replication's outcomes.

All16 atomic single-row/candidate pairs are trained in base rendering. Each
matching pair appears three times per epoch and each nonmatching pair once,
giving96 trials per arm. Every trial supplies one pulse to each compartment;
the supervised valence determines which is before versus after the cue.
Inconsistent timing assignments are exactly balanced within each image.

Test all24 unordered two-row/candidate compositions absent from training,
represented as48 ordered rows/candidates in four renderings. The template
parser and row pooling supply view/order invariance, yielding24 distinct neural
inputs. Each distinct input is simulated from reset once per frozen evaluation;
the other records explicitly identify their measured-input aliases. Nothing is
reused across trained states, arms, mappings, or erasure. Before this change,
experiment004 independently simulated1184 evaluation presentations: all1008
repeats matched the full spike-count hash of their identical input/state.

The fixed gate requires every mapping/order to reach >=90% balanced accuracy,
>=85% for each class, candidate, and view, and >=25 percentage points above
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
