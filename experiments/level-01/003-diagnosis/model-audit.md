# Step 1: scientific model audit

Reviewed 2026-09-10. This is a source/code comparison, not a simulation result.
Biological mismatch does **not** by itself establish the cause of either pilot's
failure. Causal claims require the accompanying intervention experiments.

Audited identities: Sudokufly `e20b034d07d2f09c2bf3e4f973a1d05bfd8aa47b`;
Stonkfly `78ef3e05ab0fa086032098558d893667068944a0`, loaded from
`/Users/htomar/Documents/Learning/sudokufly/.upstream/stonkfly`.

## What the source paper establishes

[Huang, Luo et al. (2024)](https://www.nature.com/articles/s41586-024-07819-w)
model odor conditioning through three mushroom-body compartments, using nine
units for a given odor pair. Graph connectivity constrains interactions, while
functional strengths are fitted to 86 spike-rate measurements. Conditioning uses
a three-second odor-to-shock onset interval. PPL1 excitation and suppression both
matter; sucrose suppresses several PPL1 types. These are not demonstrations of a
whole-connectome LIF agent learning arbitrary actions. See Figure 5 and Methods,
“Computational model.”

## Changes to the learning equation

The [supplementary appendix](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07819-w/MediaObjects/41586_2024_7819_MOESM3_ESM.pdf)
uses baseline-subtracted KC **and** DAN activity, distinct trace amplitudes and
decay rates (equations 3.2–3.5, p. A9), and a nonzero fitted simultaneous-pairing
amplitude `A_AH(0) = -7.12` in the three-module model (equation 5.18 and Table 3).
Its odor representations are separate by construction (p. A5). It fits effective
weights rather than setting their magnitude from synapse counts (p. A5).

The local implementation differs:

| Code evidence at the pinned commits | Actual implementation |
| --- | --- |
| [rule.py](/Users/htomar/Documents/Learning/sudokufly/.upstream/stonkfly/stonkfly/neural/rule.py:14), lines 14–23, 39–48 | Both traces have equal normalized one-second dynamics. |
| [brain.py](/Users/htomar/Documents/Learning/sudokufly/.upstream/stonkfly/stonkfly/neural/brain.py:177), lines 177–180, 331–337 | DAN baseline defaults to zero; KC spike rates are uncentered. |
| [sudokufly.py](/Users/htomar/Documents/Learning/sudokufly/sudokufly.py:262), line 262 | Neither baseline nor tonic current is supplied by the pilot. |
| [circuit.py](/Users/htomar/Documents/Learning/sudokufly/.upstream/stonkfly/stonkfly/neural/circuit.py:15), lines 15–45 | Reward/PAM11 and aversive/PPL101 populations share one rule; contact fractions distribute modulation. |
| [sudokufly.py](/Users/htomar/Documents/Learning/sudokufly/sudokufly.py:43), lines 43–64 | Expansion adds targets with any direct DAN contact and normalizes each target's total modulation to one; baseline gains remain unchanged. |

Pinned upstream copies: [rule](https://github.com/nftechie/stonkfly/blob/78ef3e05ab0fa086032098558d893667068944a0/stonkfly/neural/rule.py#L14-L48),
[rate inputs](https://github.com/nftechie/stonkfly/blob/78ef3e05ab0fa086032098558d893667068944a0/stonkfly/neural/brain.py#L331-L337),
[compartment selection](https://github.com/nftechie/stonkfly/blob/78ef3e05ab0fa086032098558d893667068944a0/stonkfly/neural/circuit.py#L15-L45).

**Mathematical consequence, not a measured pilot explanation:** for one plastic
edge, let `D` be its gain-weighted DAN rate. If `D(t) = a*K(t)` and traces start
at zero, equal trace filters imply `Dbar = a*Kbar`. Consequently
`q = eta*(K*Dbar - D*Kbar) = 0` at every update. Constant rates also yield zero
drive after equilibration. The symmetric implementation therefore removes a
class of synchronous association supported by the paper's asymmetric rule.
Delayed feedback breaks proportionality, so this does not imply that all pilot
updates vanish or that unequal trace constants alone will fix learning.

## DNp20 is an engineered output channel

The [Male Adult Nerve Cord study](https://elifesciences.org/articles/96084),
Figure 4 discussion, identifies DNp20 as DNOVS1 and describes electrical coupling.
[Suver et al. (2016)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5125229/), Results,
“Descending neurons encode distinct rotation axes,” p. 11772, reports:
“We found no evidence of action potentials in the large-diameter DNOVS1 cell”.
Responses were graded membrane-potential changes; dye coupling supported
connections to VS cells and likely neck motor neurons. These observations concern
the studied Drosophila preparation, not every possible biological condition.

PMC direct access intermittently returned a browser challenge. The passage was
retrieved through the search index of that primary article and independently
checked in the [same primary paper reproduced on ResearchGate](https://www.researchgate.net/publication/310474928_An_Array_of_Descending_Visual_Interneurons_Encoding_Self-Motion_in_Drosophila).
The [publisher PDF](https://www.jneurosci.org/content/jneuro/36/46/11768.full.pdf)
returned HTTP 403 during this audit; it is an alternative locator, not an
independently inspected copy.

In contrast, [sudokufly.py](/Users/htomar/Documents/Learning/sudokufly/sudokufly.py:125)
lines 125–138 and 265–268 select DNp20 **spike counts** and assign right-minus-left
activity to accept/reject. The [native kernel](https://github.com/nftechie/stonkfly/blob/78ef3e05ab0fa086032098558d893667068944a0/stonkfly/neural/kernel.cpp#L46)
uses a spike threshold for these cells. This is an artificial interface; the
literature does not validate it as a learned binary-choice channel. It may still
be useful computationally, but that must be demonstrated within this simulator.

## Implications for continued Step 1 work

[Aso and Rubin's experiments](https://pmc.ncbi.nlm.nih.gov/articles/PMC4987137/)
demonstrate compartment-specific learning and memory-updating rules. One common
rule across more connections is therefore not automatically a more faithful
model. Anatomical [visual inputs to KCs](https://www.nature.com/articles/s41467-024-49616-z)
also do not establish that the simulator encodes the chosen patterns adequately.

Measure cue specificity at the plastic KC inputs; separate pre-feedback,
feedback, and settling updates; and establish which memory pathways can change
the decoder in each direction. Compare baseline centering and timing asymmetry
as separate controlled hypotheses. None of these literature findings proves
that adding more connections or changing the decoder will complete Step 1.
