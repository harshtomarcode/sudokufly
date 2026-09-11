# Development: label-blind calibration of prior learned memories

Experiment 007 reaches perfect paired behavior, but incorrect feedback also
helps the already trained source substantially. Its incremental-learning gate
remains failed. This experiment asks a different causal question: after the
same common weakening, are the ORIGINAL Step 2 associations still necessary
for accurate one-blank judgments? It returns to the original transfer controls
and retains every numerical performance, subgroup, precision, completion,
25-point control advantage, and erasure requirement.

Restore each original Step 2 arm's own saved W/u/w: paired, frozen, no-feedback,
and inconsistent, under both mappings and source orders. Every arm receives
exactly the same fixed calibration, including the formerly frozen source arm:
two rounds through all 16 pair groups in their saved index order. For each group,
reset electrical state retaining memory; drive its preset eight KC representatives
for 500 ms with weights frozen; stimulate BOTH DAN compartments together for
200 ms at current 20 with learning enabled; then allow 250 ms passive relaxation.
Keep the source eta 0.00075, KC current 30, and output current 5.5. All synaptic
updates come from the unchanged local rule on the original 7,835 eligible edges.

No board, label, action, or target mapping selects these calibration events.
The schedule does not branch on neural scores. Record all KC/DAN activity and
phase memories. Simultaneous DAN stimulation is a new exposure. This is common
weakening through the rate rule, not necessarily uniform multiplicative gain
scaling; clipping and gain differences must be reported. Two rounds are fixed
before evaluation, not selected from intermediate candidate scores.

Then use the original 24 simultaneous KC inputs, fixed 500 ms MBON decoder,
1.625 Hz offset and 2 Hz deadband. The same calibrated source control arms are
compared with the paired source; no extra board-labelled teaching occurs.
Stage erasure restores each arm's OWN source W/u/w and responses, with full
untrained erasure and nonplastic preservation checked separately.

The design is informed by earlier labelled development results. Passing would
show transfer of existing internal comparison memories under an engineered
one-blank interface, not newly acquired board-specific knowledge or an untouched
zero-shot benchmark. Reserve the 192-grid family until all development gates
pass and code/parameters/memories are committed. Both families still alias the
same 16 neural inputs, so confirmation tests board coverage rather than new
neural representations.

```sh
.venv/bin/python one_blank.py --split development --per-pair 8 --timing simultaneous --calibration-epochs 2 --teaching depression --out experiments/level-03/008-common-weakening/development
# Only after development passes:
.venv/bin/python one_blank.py --split heldout --per-pair 8 --timing simultaneous --teaching depression --conditioning-source experiments/level-03/008-common-weakening/development --out experiments/level-03/008-common-weakening/heldout
```
