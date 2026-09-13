# Learn a visible Undo action

The frozen baseline is preserved at `649e178`. This separate development
experiment trains a new state/action association through the same 7,835
existing KC→MBON plastic edges. It keeps the complete connectome, local learning
rule, currents, 500 ms observation and fixed decoder unchanged.

## What is supplied and what is learned

The display shows a highlighted target and a visible UNDO operation. Four
generic peer-template presence bits select one of 16 equally sized groups of
16 sensory KCs. These 256 KCs exclude every KC in the original placement bank.
Selection uses original anatomical contacts to both outputs, with a balanced
partition and no neural task outcomes. All 16 presence patterns are routed
identically in form; the encoder never computes a dead-end label.

**This representation supplies a lookup table of distinguishable contexts.**
The fly must learn their action associations: accept Undo when all four peer
symbols are present, reject it for the other 15 patterns. Every pattern is
trained, so successful recall is not learned Boolean composition or transfer
to unseen neural patterns. Visual recognition and target attention remain
engineered. No new edges or fitted output layer are introduced.

## Frozen protocol before neural training

- Two inherited Step 3 histories × both output mappings × four arms. Every arm
  within a condition starts from the same **paired** Step 3 memory. These warm
  controls isolate the new training, rather than the whole previous curriculum.
- Eight epochs of 30 trials. Each epoch presents the all-four pattern 15 times
  and every other pattern once. Cue order is seeded and saved before training.
- Every trial receives the existing bidirectional teaching sequence: cue 500 ms
  frozen; target DAN 200 ms learning; passive 250 ms; electrical reset retaining
  memory; opposite DAN 200 ms frozen; cue 500 ms learning; passive 250 ms.
- Frozen controls receive the correct pulses with frozen weights. No-feedback
  controls omit both pulses but retain active learning and passive windows.
  Inconsistent controls shuffle an exactly equal number of both labels over
  **all occurrences of each pattern**: 60/60 for the repeated pattern and 4/4
  for every other pattern. Both pulsed compartments receive equal total dose.
- No response-dependent stopping, rehearsal, old-synapse clamping or restoration
  during training. Existing memory undergoes about 288 simulated seconds of
  passive relaxation in active windows, so retention is a substantive test.
- Evaluate all 121 physical inputs (105 placement plus 16 Undo) from electrical
  reset with memory frozen. Verify full-network weight hashes across each batch.
  Restore inherited W/u/w for stage erasure, then original memory for full
  erasure; remeasure all 16 Undo and 16 familiar placement inputs exactly against
  their references. Check all nonplastic weights independently.

The new-association gate requires balanced accuracy ≥90%, each class recall
≥85%, and ≥25 percentage points over every warm control, in all four conditions.
Retention requires all 16 familiar placement actions to remain correct.
Report the broader placement occupancy scores separately, preserving the failed
001 prerequisites. Timeouts count as errors; the 15:1 Undo class imbalance makes
plain accuracy inadequate.

## Sequential recovery

Use the same 160 development puzzles and both predeclared placement policies.
Scan currently empty cells in row-major order, trying digits 1 through 4 and
immediately committing the first neural acceptance. Always offer Undo after
that digit cycle, including after an accepted placement. Its highlighted target
can therefore be filled. Accepted neural Undo pops the latest nongiven placement;
then the fixed global scan continues. No host legality checks, automatic Undo,
solution access, tried-candidate memory or per-branch cursor selects actions.

Stop when full, at 16 sweeps or 1,024 decisions, or when an identical board and
stack recur at a sweep boundary. The last condition only ends a deterministic
loop: frozen, reset inference and an identical menu would repeat forever.
It supplies no alternative action. Grade validity only after the episode.
Save every image/input reference, neural action and board/stack transition in
`episodes.jsonl.gz`; identical physical inputs explicitly reuse measured frozen
responses and do not count as independent neural observations.

Perfect placement and Undo judgments solve 159/160 development cases under this
interface: all easy cases, 32/32 three-blank traps and 31/32 four-blank traps.
`b4-00cae9940eafa634` loops. This data-only interface check establishes feasibility,
not neural success. Require actual neural solve rates ≥90% in **each** available
blank-count/easy-or-trap stratum; report both policies.

This development experiment cannot complete Step 5. Successful association
recall, old-skill retention, robust placement, actual recovery and reserved-family
confirmation are separate requirements. The reserved puzzles are not evaluated
here. Two deterministic saved histories are not independent biological samples.

```sh
.venv/bin/python learn_undo.py --out experiments/level-05/002-learned-undo/development
```

Freeze the source and this protocol in Git before running. Preserve all outcomes,
including failed retention or controls, before choosing another experiment.
