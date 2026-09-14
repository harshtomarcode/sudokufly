# Joint placement and Undo rehearsal

Experiment 003 preserves Undo learning with less decay, but still fails
retention in three conditions and fails occupancy gates in every condition.
This pilot starts from its four saved paired memories. It supplies no new
neurons, edges, sensory features or output parameters.

Predeclare capped-24 as the primary placement policy based on 001, where it
had fewer errors. Eight-per-pair remains in every frozen probe report but is
not the selected sequential policy. Capped-24 uses different nested KC subsets
at different peer counts: four-peer inputs drive three cells per hemisphere
per pair, while familiar three-peer inputs drive four. This provides a possible
way to strengthen the shared core for rejection while rehearsing other
contexts. It is a hypothesis tested by actual neural training, not a guarantee.

Each seeded epoch presents all 60 nonempty capped placement contexts and all
16 Undo contexts once. Observe for 500 ms with frozen memory. If the label-signed
decoder score is below **3 Hz**, apply the existing bidirectional dopamine
teaching sequence. Otherwise keep the whole trial frozen. The inference
threshold remains **±2 Hz**, and currents, learning rate, decay and the local
rule remain unchanged. Labels affect teaching only. There is no forced old
weight restoration, selective clamping or replacement decision head.

Evaluate all 121 physical inputs after each epoch and save every checkpoint.
Run at most eight epochs per condition. Stop at the first epoch satisfying:

- Capped placement nonempty balanced accuracy ≥90%, every present class at
  each nonempty occupancy ≥85%, and ≥25 points above each original-history
  control from 001. In particular all four all-peer rejections must be correct.
- All 16 familiar placement judgments correct; timeouts remain errors.
- Undo balanced accuracy ≥90% and both class recalls ≥85%.
- Actual development recovery ≥90% in each of the five available strata.

The recovery menu and pixel encoders are unchanged. Only evaluate development
episodes after the joint judgment gate passes, or at the final epoch if it
never passes. Preserve every attempted epoch, failed case and stopping decision.
Stage erasure restores the inherited 003 memory, full erasure restores original
memory, and both are evaluated exactly over all 121 inputs. Verify every frozen
full-network weight hash and all nonplastic weights.

This is a **paired-only checkpoint-selection pilot**. It cannot claim a new
control-dependent pass or finish Step 5. A passing candidate must undergo
controlled reproduction of the complete new curriculum, followed by frozen
reserved-family confirmation. A 25-point gain over already strong warm controls
on overall placement is mathematically inappropriate; new occupancy learning
must additionally be checked on the previously failed all-four-peer subset.
The empty-peer input stays silent and outside the explicit nonempty gate.

```sh
.venv/bin/python joint_sudoku.py --out experiments/level-05/004-joint-rehearsal/development
```

Freeze source and protocol in Git before running. Keep experiments 001–003 and
their original source commits available; no thresholds change after results.
