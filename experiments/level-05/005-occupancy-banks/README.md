# Separate sensory banks for observed peer counts

Pilot 004 failed all four conditions. This pilot changes sensory routing only:
generic candidate/peer identities for one, two and four distinct peers use
three disjoint banks of 256 existing KCs. The original three-peer inputs and
Undo inputs remain identical. Banks are selected deterministically from
original anatomical contacts, excluding both previously used banks, before
loading learned memories. No neuron, edge or plastic connection is added.

The pixel encoder supplies the observed number of distinct peer symbols; it
does not compute candidate equality, legality or a desired action. This is
engineered count-dependent routing, not a claim that the fly learned count
invariance. Stimulation remains 0/16/24/24/24 KCs for counts 0/1/2/3/4, with
the same currents, decoder, dopamine rule and passive decay.

Start from the same four 003 memories. Keep 004's exact 76-context curriculum,
seeded order, teaching margin of 3 Hz, eight-epoch maximum and first-pass
stopping. Select the first checkpoint with ≥90% nonempty placement balanced
accuracy, ≥85% every present class at every nonempty count, 16/16 familiar
judgments, Undo ≥90% balanced accuracy/≥85% each class, and ≥90% actual
development recovery in each stratum. Timeouts are errors. Empty inputs remain
silent and outside the explicit nonempty gate. The fixed action menu, stack,
cycle detection and recovery budgets are unchanged.

Retain the original 121 diagnostic inputs and measure all 44 additional inputs
from reset with frozen memory, after inheritance and every epoch. Save every
checkpoint. Verify exact stage/full erasures and full-network weight hashes.
The original policies remain reported as diagnostics. Their old controls
cannot serve as controls for the new inputs: new-policy control gains remain
explicitly unassessed in this paired-only pilot.

Step 5 cannot pass here. A successful pilot requires controlled reproduction
of the entire new curriculum from pre-Undo paired Step 3 memory, then frozen
reserved-family confirmation. Preserve all failed runs. Do not inspect reserved
performance or change any threshold while choosing development checkpoints.

```sh
.venv/bin/python joint_sudoku.py --separate-occupancies --out experiments/level-05/005-occupancy-banks/development
```

Freeze this source and protocol in Git before execution.

## Result

Source frozen at `075367c`; runtime 853.22 seconds. All four conditions learned
**all 44 newly routed judgments correctly**, and final Undo recall remained
100%. Familiar retention nevertheless ended at 12/16, 13/16, 13/16 and 13/16.
Every condition therefore failed the unchanged gate after eight epochs.

Final nonempty placement balanced accuracy was 93.08%, 94.64%, 94.64% and
94.64%; those aggregate scores conceal failed familiar judgments. The fixed
menu solved only 4, 4, 1 and 4 of 160 development puzzles, respectively.
New input learning alone is insufficient for sequential performance.

The complete run retains 32 checkpoints, 2,432 trial observations and 7,425
frozen neural evaluations. It supports separate count-dependent sensory routes
as a useful intervention in this pilot, while the original three-peer teaching
method still requires repair. It does not yet establish controlled necessity
for the new learning or any reserved-family success.

The independent [audit](audit.json) verifies all source/artifact hashes,
608 teaching events, 45 frozen full-weight batches, exact erasures, anatomical
bank selection and all 640 episodes (11,911 actions). The reports are
[bound to the raw summary](audit-files-sha256.json).
