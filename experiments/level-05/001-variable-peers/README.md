# Variable-peer probe and sequential baseline

## Predeclared questions

Step 4 supplied exactly three distinct peer symbols to the learned fly. A
sequential puzzle can expose fewer symbols, repeated copies, or all four at a
dead end. Test those inputs before claiming sequential competence, keeping the
saved Step 3 histories, dopamine model, current 30, output current 5.5, 500 ms
observation and fixed `MBON11 - MBON07 - 1.625 Hz` decoder unchanged.

The pixel-only adapter retains target-unit attention and independently permuted
candidate/peer templates. It pools repeated peer identities once, without ever
comparing candidate identity with a peer or computing legality. Two routing
policies are fixed in advance and both reported:

| Policy | 0 distinct peers | 1 | 2 | 3 | 4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Eight KCs per pair | 0 | 8 | 16 | 24 | 32 |
| Capped 24-KC budget | 0 | 16 | 24 | 24 | 24 |

The second chooses `min(8,12//n)` preset cells per hemisphere per pair. Both
preserve the successful three-peer inputs exactly. Empty context has no KC
drive and is not silently accepted; adding a learned empty-context percept
would require a separate representation and conditioning experiment.

Each policy covers all 64 candidate/subset contexts: 32 legal and 32 conflicting.
Their union has 105 physical neural inputs, including the shared empty input.
Base, shifted and smaller-glyph renderings must map identically. Frozen
inference resets electrical state and retains W/u/w; every original-history
control is restored separately. Full memory erasure must restore exact baseline
spikes, traces and latent state, and preserve all nonplastic weights.
Each complete frozen-evaluation batch also compares the full network-weight
hash before and after evaluation, before any erasure could conceal a change.
All familiar three-peer responses must exactly reproduce the Step 3 records.

A nonempty-policy gate requires every saved order/mapping to achieve balanced
accuracy ≥90%, each present class's recall at every nonempty occupancy ≥85%,
and ≥25 percentage points over each original-history control. Empty and
all-four contexts each have only one class, so report class recall explicitly
rather than meaningless class-balanced averages. This gate alone cannot pass
the full stage.

## Actual sequential episodes

Enumerate all 288 complete grids and all masks with two, three or four blanks.
Deduplicate partial boards and exclude multiple-completion puzzles during
dataset construction. The unique parent grid determines the existing
development/heldout structural-family split. No solution or grader information
enters the runtime action choice.

| Blanks | Unique puzzles | Ideal local greedy solves | Dead ends |
| --- | ---: | ---: | ---: |
| 2 | 34,560 | 34,560 | 0 |
| 3 | 161,280 | 160,128 | 1,152 |
| 4 | 522,624 | 508,128 | 14,496 |

Construct easy/trap strata using a separate perfect immediate-legality greedy
diagnostic. Select the lowest 32 fixed SHA-256 board hashes in each existing
blank-count/split/stratum group. This supplies 160 development cases and 160
reserved cases, with no fabricated two-blank traps. Selection never uses neural
results. Record full-universe counts/hashes, ranking, parent grids and grader-only
diagnostic traces. A 90% aggregate solve gate on four blanks would be inadequate:
ideal greedy already solves 97.23% without any undo.

For both routing policies and every source arm, run development episodes with
row-major empty targets and candidates 1,2,3,4. Every neural acceptance is
immediately placed, including any incorrect choice. No legality filter, hidden
solution, repaired action, or undo is used. An unchanged complete sweep is a
deterministic stall; otherwise stop when full or after four sweeps. Grade rows,
columns, boxes and preservation of givens afterward. Record every rendered
observation hash, input reference, action, and board transition. Reuse one
measured frozen response for identical neural inputs as an explicit alias.

**This is a prerequisite and greedy baseline, not a complete Step 5 agent.**
Undo is unimplemented and the full-stage gate remains false regardless of
these scores. The reserved sequential cases are saved but not evaluated in
this exploratory run. Failed recovery cases must remain visible separately
from easy successes. No new learning or newly learned spatial rules are claimed.

```sh
.venv/bin/python sequence_sudoku.py --out experiments/level-05/001-variable-peers/development
```

The output directory must be new. Freeze this source and protocol in Git before
running, and preserve all results before changing a policy or teaching rule.

## Result

Source frozen at `b24cba9`; the completed development run took 405.15 seconds.
Both input policies failed the predeclared nonempty gate in all four saved
history/mapping conditions. In particular, none correctly rejected the
all-four-peer contexts, and empty contexts were never accepted. The broad
balanced accuracies below therefore do not establish occupancy robustness.

| Mapping | Eight-per-pair balanced accuracy, nonempty | Capped-24 balanced accuracy, nonempty |
| --- | ---: | ---: |
| 0, either history | 93.75% | 91.96% |
| 1, either history | 75.89% | 93.75% |

Across both policies and all four paired conditions, **768/768 easy episodes
solved and 0/512 trap episodes solved**. Every original-history control solved
zero puzzles. These are replays on the same 160 development puzzles, using
measured deterministic responses; they are not independent puzzle samples.

Independent audit verified all 14 artifact hashes, 16 memory references, 33
full-network weight checks, 3,465 neural records, 528 exact familiar Step 3
replications, 32 arm/policy summaries and 5,120 episode transition histories.
The failure is substantive, with no scoring or routing discrepancy found.
No new training occurred. The next experiment must test a learned Undo action
and retain these failed placement prerequisites in its interpretation.
