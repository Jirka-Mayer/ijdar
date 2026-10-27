# Smashcima data generation for `smc` models

This folder contains the `smc` python package, which takes a solo-staff zeus dataset and produces its variant with images synthesized by [Smashcima](https://github.com/OMR-Research/Smashcima). It is derived from the ICDAR 2026 code: https://github.com/Jirka-Mayer/icdar26/tree/main/app/datasets/smashcima

It has its own virtual environment (Python 3.11+, separate from `.venv-zeus`, which is pinned to 3.10 by TensorFlow):

```bash
python3 -m venv smc/.venv
smc/.venv/bin/pip install -e smc
```

Smashcima assets are cached in `smc/smashcima_assets` (gitignored). Install them once before running anything in parallel:

```bash
smc/.venv/bin/smc install-assets
```

> **Note:** The MUSCIMA++ download URL used by Smashcima 1.1.2 is dead (LINDAT migration returns an HTML page). Copy the `MuscimaPP` and `MuscimaPPGlyphs` bundle folders from an existing installation (e.g. `~/ufal/icdar26/smashcima_assets`) into `smc/smashcima_assets` before running `install-assets`.

The OmniOMR glyphs (bundle `OmniOmrIjdarGlyphs`) are extracted from the page-level MuNG files of the **train split** of the OmniOMR MusiCorpus dataset at `~/musicorpus/UFAL.OmniOMR` (override with the `SMC_OMNIOMR_MUSICORPUS` env variable). DPI is read from the `metadata.json` files.


## Synthesis

Run from the repository root (MuseScore is taken from the `musescore/` folder in the working directory):

```bash
smc/.venv/bin/smc synthesize \
    --input-dataset datasets/olimpic-synthetic \
    --output-dataset datasets/olimpic-smc-gboth \
    --glyphs both \
    --copies 4
```

For each sample of the input dataset (all splits), the output dataset contains:

- `.musicxml` and `.lmx` with **all key and time signatures removed** (Smashcima cannot render them). Key and time changes are deleted, the header key becomes `fifths:0`, the header time signature is removed. Everything else that Smashcima does not render (slurs, tuplets, articulations, ...) is kept in the annotation as is.
- `_rendered.png` the normalized MusicXML engraved by MuseScore (same as `zeus render`), for comparison with Smashcima. Its width also determines the width of the Smashcima images.
- `_copy1.jpg`, `_copy2.jpg`, ... the Smashcima images, each with a different seed. With `--glyphs both`, each image randomly uses either MUSCIMA++ or OmniOMR glyphs.

The `samples.*.txt` files are copied from the input dataset, samples without an image are skipped by `zeus pickle --benevolent`:

```bash
zeus pickle --image-suffix '_copy1' --benevolent datasets/olimpic-smc-gboth/samples.train.txt
```

Already existing images are skipped, so to add more copies later, just re-run with a larger `--copies`. For local debugging, use `--debug-samples 10 --copy-original-images`.

On the cluster, run in parallel from the head node:

```bash
bash smc/synthesize-on-cluster.sh datasets/olimpic-synthetic datasets/olimpic-smc-gboth both 4
```
