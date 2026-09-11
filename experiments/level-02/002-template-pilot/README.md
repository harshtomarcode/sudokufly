# Untrained template-routing probe

No reinforcement was performed in this probe. Four unique normalized glyph
patches were deduplicated from the base training images and ordered by pixel
hash. Candidate and row banks were independently permuted. All 16 Cartesian
template pairs received disjoint groups of 16 existing KCs, eight per hemisphere,
using serpentine anatomical-rank strata. No pair label or equality computation
was used to allocate neurons. This is explicit fixed template recognition,
not learned fly vision and not a trained decision head.

The untrained raw MBON difference ranged from -0.5 to +7 Hz, with considerable
between-pattern variation. The prescribed deadband was 2 Hz; offset was the
unlabelled mean. This motivated further label-blind anatomical balancing before
running reinforcement. No Step 2 success or failure gate was evaluated here.

```sh
.venv/bin/python compare_symbols.py probe --task symbols --encoder templates --eta 0.00075 --epochs 4 --threshold-hz 2 --training-seed 20260913 --out experiments/level-02/002-template-pilot/probe
```
