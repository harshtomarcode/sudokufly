# A fly playing Sudoku

[Open the public demo](https://harshtomarcode.github.io/sudokufly/), hosted on
GitHub Pages. Play, neural activity, brain rotation and Reset Sudoku work entirely
in the visitor's browser.

Open `index.html` in a browser. Keep `data.js` and `fly.png` beside it. Everything
runs locally, without a package install or a live neural simulator. Alternatively,
from the repository root:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory demo
```

Open http://127.0.0.1:8765. Play/Pause runs the recorded decisions, Next decision
steps through them, and Reset Sudoku restores the original puzzle and stops
playback. Drag the brain close-up to rotate its measured 3D coordinates. Optional
synaptic links connect the known source and target cells.

## Careful choices

When the committed Step 6 development pilot passes its controls, the exporter
adds **Careful choices** as the default replay. The fly learns Place/Defer through
existing synapses, accepting locally forced placements and deferring ambiguous
ones. A fixed selector compares the neural readout of every digit in every empty
cell, selects the highest accepted score, and stops if nothing is accepted. It
does not use a Sudoku legality filter or the puzzle solution to choose a move.

This replay animates the four chosen placements. The total of 40 candidate
assessments stays visible; expand the table to inspect all offers for each move.
The brain animation shows the chosen offer's recorded activity. Evaluations of
other offers are not animated, and the score is not a probability of success.
The board is the first lexicographic four-blank development trap,
`b4-0009393db5453f62`, using the original dataset's stratum. The visual example was
chosen after training to show ambiguous offers, without filtering on new policy
outcomes. Its new responses
and synaptic weights are bound to the selected pilot checkpoint, with separate
input identifiers so they cannot overwrite the original Step 5 recordings.

This is development-only evidence from one inherited training history and both
answer mappings. It does not complete Step 6 or demonstrate general Sudoku
planning. The original three Step 5 replays remain available for comparison.
See the [prospective pilot protocol](../experiments/level-06/001-cautious-choice/README.md).

## Publish an update

GitHub Pages publishes the root of `codex/github-pages`. That dedicated branch
contains only `index.html`, `data.js`, `fly.png` and an empty `.nojekyll` file;
its initial deployment is `de98146`, exported from source commit `7cbc71f`.
Pushing updated display files to that branch triggers another deployment.
Changes to `main` or `demo/` alone do not update the public site.

From a checkout containing the reviewed demo, use an unused temporary directory:

```sh
git fetch origin codex/github-pages
git worktree add /tmp/sudokufly-pages codex/github-pages
git -C /tmp/sudokufly-pages pull --ff-only
cp demo/index.html demo/data.js demo/fly.png /tmp/sudokufly-pages/
touch /tmp/sudokufly-pages/.nojekyll
git -C /tmp/sudokufly-pages add index.html data.js fly.png .nojekyll
git -C /tmp/sudokufly-pages commit -m "Update fly Sudoku demo"
git -C /tmp/sudokufly-pages push origin HEAD:codex/github-pages
git worktree remove /tmp/sudokufly-pages
```

After the repository's Pages build finishes, check the public URL, playback and
Reset Sudoku. The simulator, research data and exporter are not needed to serve
the page. Keep source changes on a normal review branch; the deployment branch
has a separate static-only history.

## What is real

The original Step 5 examples contain 42 decisions, 18 frozen neural traces and
1,069 distinct KC→MBON connections, all from the audited Step 5 reserved run:
seed 20260919, mapping 0, paired arm, base view. The examples are the shortest
recorded recovery, straightforward four-blank solve, and remaining loop in their
respective pools, with case ID as the tie-breaker. They are illustrations, not
an additional evaluation sample.

Cell-body positions come from `somaLocation` in the original, checksum-verified
MaleCNS annotations. All available positions of displayed neurons are preserved,
with rotation and uniform scaling for display. The original Step 5 views contain
321 located neurons among 322 selected. KC 110815 has no
recorded position: its spikes still contribute to the replay, but it is explicitly
unlocated on recovery decision 3 and loop decision 1. The faint background shows
all 4,050 located Kenyon cells plus 2,000 sampled brain cells. No VNC cells or
invented positions are added. Background dots are anatomical context, not
measured silence; per-cell activity is available only for the selected input
cells and six readout neurons. Dataset axis values are preserved without claiming
anterior/dorsal polarity. See the [MaleCNS data documentation](https://male-cns.janelia.org/download/).

The fly body is an AI-generated illustration, not a registered microscopy image.
Its head overlay locates the brain illustratively; the enlarged point cloud
preserves relative measured soma coordinates. Lines indicate anatomical
connectivity, not reconstructed neurite trajectories or measured causal signal
flow. Light follows recorded spike bins. No new learning occurs in the demo.

The task still uses supplied sensory recognition, routing, board scanning and
an Undo stack. Favorable warm controls solve all 160 reserved puzzles; the
trained policy solves 158. See the [complete experiment](../experiments/level-05/README.md).

## Rebuild the recorded data

```sh
.venv/bin/python demo/export_replay.py
```

The exporter checks recorded artifact/source hashes, graph and annotation hashes,
checkpoint weights and latent state, neuron identities, trace-derived rates and
choices, every board/Undo transition, clue preservation and final validity. The
committed data makes the demo usable without the full research dataset.

Browser checks cover all 46 displayed board transitions and readout rates,
all 40 cautious-policy candidate assessments, correct Undo highlighting,
solved/loop endings, pause/resume, reset during playback, the unlocated-neuron
notice and responsive layout, including the new table at 390 px width.

## Fly artwork

`fly.png` was generated with the built-in image-generation tool. It is a visual
asset only; neuron locations and activations are overlaid separately from data.

<details><summary>Generation prompt</summary>

Use case: scientific-educational. Asset type: transparent-background realistic fruit fly illustration for an interactive neuroscience Sudoku demo. Create ONE isolated adult male Drosophila melanogaster, full body including six slender legs, two delicate translucent wings, antennae and reddish compound eyes. High fidelity macro photography / polished natural-history 3D rendering, realistic tan thorax, striped dark abdomen, fine hairs and wing venation. STRICT composition: dorsal top-down view, the fly faces LEFT, head at approximately x=25%, y=50% of the square image, body axis horizontal, abdomen trailing to the RIGHT at x=70%, wings angled toward upper-right and lower-right; wings separated enough to see thorax. Forelegs reach to the left as if interacting with a game surface. Entire fly comfortably inside image with generous transparent margin, no cropping. Soft neutral studio lighting, subtle depth. The central head capsule BETWEEN the red compound eyes should be pale translucent smoky amber so a separately coded neuron visualization can be overlaid there. Do not draw neurons, nervous system, lights, paths, labels, text, board, grid, props, or background. Actual alpha transparency, not a checkerboard. This is an illustrative fly body only, not the measured scientific data.

</details>
