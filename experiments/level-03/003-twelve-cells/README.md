# Development: 12 sensory cells

The 24-cell and 18-cell transfer assays failed the unchanged rejection gates.
This last simple population-size probe uses four existing representatives per
pair, two per hemisphere from the fixed saved ordering, for 12 total KCs.
Every pair receives identical treatment. All weights, currents, decoder values,
development boards, controls, and performance criteria remain unchanged.
No new training occurs and the held-out family remains reserved.

```sh
.venv/bin/python one_blank.py --split development --per-pair 4 --out experiments/level-03/003-twelve-cells/development
```

## Outcome: mapping-dependent failure

Both source orders reach 100% on mapping 1, but only 54.17% balanced accuracy
on mapping 0, with 8.33% rejection recall and 57.14% acceptance precision.
Mapping 0 falsely accepts candidate 4 on all boards; ascending scans still
complete every board because a correct earlier acceptance stops the scan.
This illustrates why scan completion alone is insufficient. All memory and
erasure checks pass. Runtime was 71.44 seconds. The gate remains failed and
the held-out family remains reserved. Population size alone is not a robust
solution under both action assignments.
