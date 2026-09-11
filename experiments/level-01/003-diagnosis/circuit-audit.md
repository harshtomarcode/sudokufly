# Static circuit and saved-memory audit

Date: 2026-09-10. This audit reads the committed experiments 001/002 and the
pinned local MaleCNS graph. It does not run neural simulations, retrain weights,
or modify the original results. Structural observations below motivate causal
tests; they are not evidence that a particular pathway was active in a trial.

## Scope and sources

Both pilots already simulate the same **166,700 neurons and 25,582,938 directed
connections**. Experiment 002 changes which existing KC-to-MBON connections may
learn: 7,835 becomes 34,249. It does not add neurons, add graph connections, or
begin simulating a previously omitted part of the brain.

Sources, with paths relative to the repository root:

- `data/graph.npz`: CSR arrays `ptr`, `post`, `weight`, and `ids`. These are the
  fixed compiled baseline, not a trained snapshot.
- `data/annotations.feather`: join `bodyId` to graph `ids` for cell type, side,
  and instance. Never assume Feather row order matches graph indices.
- `data/normalized/neurons.feather`: join `source_id` to graph `ids` for the
  declared neurotransmitter class.
- `experiments/level-01/{001-visual-cues,002-expanded-memory}/mapping-{0,1}-learned-memory.npz`:
  saved `edge_indices`, effective `weights`, and latent `u/w`. Their SHA-256
  values are recorded in each committed experiment's `summary.json`.
- `sudokufly.py:expanded_memory_circuit` and upstream
  `stonkfly/neural/{circuit.py,prepare.py,transmitters.py,brain.py,kernel.cpp}`,
  pinned to upstream commit `78ef3e05ab0fa086032098558d893667068944a0`.

The parent diagnostic runner, `diagnose_step1.py`, records separate dynamic
tests. Its outcomes must be read separately from the anatomical hypotheses here.

## Calculation definitions

For snapshot edge index `e`, let `b[e] = graph.weight[e]` and `w_m[e]` be the
saved effective weight for mapping `m`. Every selected plastic baseline weight
is positive. Define:

```text
effective weight delta: delta_m[e] = w_m[e] - b[e]
efficacy delta:          d_m[e] = w_m[e] / b[e] - 1
absolute delta mass:     L1(S,m) = sum(abs(delta_m[e]) for e in S)
changed edge:            delta_m[e] != 0
```

The correlations below are Pearson correlations of `d_0` and `d_1`, using
`numpy.corrcoef`, aligned by identical saved `edge_indices`. "Changed union"
restricts to edges with `d_0 != 0 or d_1 != 0`. Both-input arithmetic uses the
saved float32 effective weights and the graph's float32 baseline. Unchanged
zeros can inflate a full-vector correlation, so the changed-union value is
reported separately. Counts use exact saved inequality, not a biological
effect-size threshold. These are descriptive statistics, not independent
replicates or a significance test.

For a selected DAN `i` and MBON `j`, contact support is
`C[i,j] = sum(abs(graph.weight[e]) for i->j edges) / 0.275`, rounded to the
underlying integer contact count. This conversion follows `prepare.py`'s
`weight = synapse_count * transmitter_sign * 0.275`. Support means contacts
from the **17 selected PAM11/PPL101 cells only**, not all dopamine neurons in
the graph. Added edges receive gains `C[i,j] / sum_i C[i,j]`; original edges
retain their original compartment-specific gains.

## Opposite assignments induce strongly related changes

| Experiment | Full-vector correlation | Changed-union correlation | Changed in both | Changed in either |
|---|---:|---:|---:|---:|
| 001, 7,835 plastic edges | 0.9793 | 0.9754 | 2,820 | 3,062 |
| 002, 34,249 plastic edges | 0.9253 | 0.9006 | 14,574 | 15,291 |

| Experiment / mapping | Potentiated | Depressed | Unchanged |
|---|---:|---:|---:|
| 001 / 0 | 2,142 | 777 | 4,916 |
| 001 / 1 | 2,958 | 5 | 4,872 |
| 002 / 0 | 11,637 | 3,163 | 19,449 |
| 002 / 1 | 14,429 | 636 | 19,184 |

In experiment 001, MBON11 accounts for 99.99% of mapping-0 absolute delta mass
and 93.35% of mapping-1 mass. MBON07 receives the remaining 0.01% and 6.65%.
Expansion changes the distribution, but the two opposite assignments still
produce closely correlated efficacy deltas.

**Hypothesis:** a common change in recurrent activity dominates part of the
response to training. This correlation alone does not prove that task-specific
information is absent: opposite classifications need not require negated
distributed weights. The original pilots also used different cue sequences,
so this comparison does not isolate label effects from sequence effects.

## Expanded gains are strong even with weak anatomical support

The expanded selection includes 44 of 97 annotated MBON cells: 19 glutamate,
16 acetylcholine, and 9 GABA. There are 4,064 annotated Kenyon cells in the graph.

| Selected-DAN contact support per MBON | Selected MBON cells | Plastic edges | Changed edges, mapping 1 | Share of mapping-1 absolute delta mass |
|---|---:|---:|---:|---:|
| At most 1 contact | 9 | 5,706 | 2,045 | 8.78% |
| At most 2 contacts | 17 | 11,991 | 4,819 | 24.39% |
| At most 5 contacts | 21 | 15,144 | 6,271 | 29.00% |
| At most 20 contacts | 28 | 19,557 | 8,518 | 57.01% |

These rows are cumulative. Normalization gives even a one-contact target total
gain one. This is an explicit unvalidated expansion assumption, not evidence
of physiological modulation strength or compartment identity. Original
MBON07/11 cells have hundreds to over a thousand selected-DAN contacts each.

Experiment 002 has absolute delta mass 4,317.26 in mapping 0 and 3,863.39 in
mapping 1. Added edges contribute 3,159.62 (73.19%) and 2,884.77 (74.67%),
respectively. The weights are model conductance coefficients; these totals
are not measured biological quantities.

Prominent targets in the successful saved mapping-1 state:

| Target | Graph indices | Declared transmitter / modeled electrical sign | Plastic edges | Absolute delta mass |
|---|---|---|---:|---:|
| MBON11 pair | 655, 1306 | GABA / inhibitory | 4,184 | 855.41 |
| MBON05 pair | 459, 130137 | glutamate / inhibitory | 1,999 | 846.65 |
| MBON30 pair | 126500, 127556 | glutamate / inhibitory | 1,621 | 331.26 |
| MBON09 cells, both annotated R | 10200, 131769 | GABA / inhibitory | 2,286 | 310.89 |

MBON05 has 11 selected-DAN contacts per cell; MBON09 has two per cell. The
model treats glutamate as inhibitory using a coarse transmitter proxy; it
does not model receptor-specific physiological effects.

## Electrical pathways and recurrent feedback

For these path calculations, define `A[i,j] = graph.weight[i->j]`, except set
the entire outgoing row to zero for neurons whose declared neurotransmitter
is exactly `dopamine`, `octopamine`, or `serotonin`. This reproduces the
default `MemoryBrain.modulation_mask`: their spikes enter the kernel's
modulatory branch and do not deliver the ordinary fast electrical weight.
Modulatory anatomical edges must not be counted as fast electrical paths.

A direct connection is a nonzero `A[i,j]`. A two-hop electrical path is a
pair `A[i,k]` and `A[k,j]` with neither coefficient zero. Path existence is
counted before signed contributions can cancel. For aggregate destination
set `D`, a signed two-hop coefficient is
`sum_k A[i,k] * sum(j in D) A[k,j]`; absolute path mass instead sums
`abs(A[i,k]) * sum(j in D) abs(A[k,j])`. These coefficients describe this
static graph. They ignore membrane state, delays, refractoriness, adaptation,
activity, and longer recurrent paths, so they are not neural gain estimates
or predictions of behavioral direction.

The decoder neurons are DNp20_R (index 48, body ID 10059) and DNp20_L
(index 146, body ID 10162).

- None of the 44 plastic MBON targets has a direct electrical edge to DNp20.
- Only six have any two-hop electrical path: MBON03_L, MBON35_L,
  MBON33_L/R, MBON12_R, and MBON20_R.
- MBON05, MBON11, MBON30, and MBON09 have neither direct nor two-hop
  electrical paths to DNp20. Longer paths exist; this is not disconnection.
- The strongest two-hop path among selected targets is MBON03_L (130138)
  → OCG01e_R (352) → DNp20_R. Its coefficients are −0.275 and +138.05.
  Its first edge represents just one anatomical contact. MBON03 has only
  27 changed input edges in mapping 1 and absolute delta mass 11.30.

The heavily changed inhibitory MBONs have strong pathways back to the KCs
through the inhibitory APL neurons. Examples, using signed graph weights:

| Source | To APL index 502 | To APL index 904 |
|---|---:|---:|
| MBON11_R, 1306 | −135.575 | −50.875 |
| MBON11_L, 655 | −62.700 | −108.900 |
| MBON05_L, 130137 | −23.100 | Other smaller paths |
| MBON05_R, 459 | Other smaller paths | −12.925 |

APL 502's aggregate outgoing electrical KC weight is −26,274.05; APL
904's is −27,680.95. Thus the model contains a
`KC → inhibitory MBON → inhibitory APL → KC` disinhibition loop. The MBONs
also directly inhibit some KCs, and MBON05 inhibits MBON11/30; opposing paths
make net effects nonlinear. Electrical MBON feedback to DAN cells, directly
and via intermediaries, can also change subsequent endogenous dopamine
activity. The presence and signs of these paths are observations.

**Hypothesis:** potentiating KC input to these MBONs changes inhibitory
feedback and can reorganize KC/DAN activity before yielding a reliable action
association at DNp20. Whether this explains a specific trial requires the
phase measurements and interventions, not this structural audit alone.

## Causal tests motivated by the audit

The diagnostic snapshot suite separately restores these groups to baseline
inside the successful mapping-1 memory: MBON05; MBON11; MBON03; targets with
at most two selected-DAN contacts; the original MBON07/11 targets; and all
added targets. All other learned weights remain intact. Electrical state is
reset and evaluation learning is disabled. The runner also zeroes latent
`u/w` for restored edges, although frozen evaluation cannot rewrite weights.

The weak-contact group consists of graph indices:

```text
765, 1665, 1861, 2550, 3477, 10200, 42758, 57641, 126295,
130138, 130281, 131044, 131769, 131887, 132551, 132955, 135166
```

These interventions ask whether a weight group's learned changes are
necessary for the saved behavior under the original observation conditions.
An effect does not establish an isolated pathway mechanism; recurrence can
make groups interact. No effect does not establish irrelevance under all
conditions. The separate training suite crosses cue order and label mapping
to test the sequence confound. The audit does not declare Step 1 passed.

## Initial sensory activity misses the baseline reward compartment

The completed phase assay (`phases.json`, baseline / vertical) supplies an
additional bounded question for static verification. Its initial observation
activates exactly the four KCs below. Joining those body IDs to the graph and
intersecting their outgoing CSR ranges with each saved plastic-edge list gives:

| KC body ID | Graph index | Annotated instance | Baseline plastic outputs | Expanded plastic outputs | Expanded outputs with nonzero PAM11 gain |
|---|---:|---|---:|---:|---:|
| 18540 | 7784 | KCg-s1_R | 2 | 19 | 7 |
| 21778 | 10679 | KCg-s1_L | 1 | 20 | 6 |
| 44069 | 30424 | KCg-d_L | 1 | 12 | 1 |
| 520206 | 130612 | KCg-d_R | 1 | 14 | 4 |
| Total | | | 5 | 65 | 18 |

All four are gamma KC types. **None has any edge to MBON07 in either plastic
selection. All five baseline plastic outputs target MBON11.** Their exact
compiled graph edges and positive baseline weights are:

| Presynaptic KC body ID | Graph edge index | Target graph index / instance | Baseline weight |
|---|---:|---|---:|
| 18540 | 4110156 | 1306 / MBON11_R | 22.000 |
| 18540 | 4110853 | 655 / MBON11_L | 0.275 |
| 21778 | 4931279 | 655 / MBON11_L | 15.675 |
| 44069 | 8863131 | 655 / MBON11_L | 8.525 |
| 520206 | 20309425 | 1306 / MBON11_R | 11.000 |

The crucial distinction is **anatomical contact versus assigned learning
gain**. MBON11_L/R do receive 21/35 anatomical contacts from selected PAM11
cells, but `circuit.identify` explicitly gives every KC→MBON11 edge zero
PAM11 gain and assigns its modulation only to PPL101. The expanded circuit
preserves those original gains. Therefore the initial active baseline KC
eligibility set has no direct PAM11-driven plasticity route. A PAM reward
pulse cannot directly update those five edges through the implemented local
rule, however many PAM spikes are generated. This is a supported circuit
explanation, not a claim that the reward stimulus failed to reach PAM neurons.

The parent's phase result corroborates that limited mechanism: baseline
vertical reward stimulation produces 270 PAM spikes during feedback, versus
zero with no pulse, while both conditions produce five KC spikes, zero PPL
spikes, the same five changed edges, and exactly the same recorded feedback
weight-change summaries (`L1 = 0.4950908124446869`, signed change
`= 0.4931281507015228`). Both conditions use only these four KCs across the
observation, feedback, and settle phases. Matching aggregate weight-change
summaries alone are not a saved per-edge equality proof; the zero PAM gains
establish the missing direct local update route independently.

Expansion gives these KCs 60 additional plastic outputs. Their expanded
target-type multiplicities are recorded below; numbers in parentheses are
counts of distinct postsynaptic cells of that type:

- **18540:** MBON04(2), 05(1), 09(2), 11(2), 12(1), 20(1), 21(1),
  22(1), 25-like(1), 29(2), 30(2), 32(1), 33(1), 35(1).
- **21778:** MBON04(2), 05(2), 11(1), 12(2), 20(1), 21(1), 22(1),
  25(1), 25-like(1), 26(1), 29(2), 30(2), 32(1), 33(1), 35(1).
- **44069:** MBON05(1), 11(1), 12(2), 20(1), 21(1), 29(2), 30(1),
  32(1), 33(1), 35(1).
- **520206:** MBON04(1), 05(1), 09(2), 11(1), 12(1), 20(1), 21(1),
  25(1), 30(2), 32(1), 33(1), 35(1).

The 18 added outputs with nonzero PAM11 gain reach MBON04, MBON05,
MBON09, MBON22, MBON26, and MBON29 cells, through the expansion's normalized
contact proxy. This creates a reward-sensitive route for the initially
active KCs while retaining the original MBON11 restriction. It does not
validate that route biologically or establish a useful action association.
Later training can recruit additional KCs, so this result concerns the
initial phase assay and does not imply that every later reward pulse is
ineffective throughout a whole training arm.
