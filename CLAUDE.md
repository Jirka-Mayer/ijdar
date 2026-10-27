# CLAUDE.md

Experiments for Jirka Mayer's final PhD thesis journal paper (likely IJDAR). Every experiment trains the Zeus OMR model on some data. The root `README.md` describes the three experiment families, each with a doc in `docs/`:

- `zod`: solo Zeus pre-trained on Dolores ([docs/solo-zeus-on-dolores.md](docs/solo-zeus-on-dolores.md))
- `ayce`: "all you can eat", all the data, lowest possible OmniOMR test SER ([docs/ayce.md](docs/ayce.md))
- `smc`: measures the effect of Smashcima synthetic training data ([docs/smashcima.md](docs/smashcima.md), sketchy and condensed; it also covers experiment naming and fine-tuning)

How every dataset is built: [docs/prepare-datasets.md](docs/prepare-datasets.md).


## Repository layout

- `datasets/`, `models/`, `logs/`, `out/`, `musescore/` are gitignored and shared by all experiments.
- The repo exists locally (laptop) and is duplicated on the ÚFAL LRC compute cluster. Training runs there via the `slurm/*.sh` scripts (one per experiment, `sbatch` from the repo root, GPU partitions `gpu-ms,gpu-troja`). The user runs cluster jobs themselves.
- `musescore/` holds the MuseScore AppImage, resolved relative to the working directory by `lmx`'s `MuseScore.resolve_linux_default()`. Commands that render therefore run from the repo root.
- `smc/` is the `smc` python package that synthesizes the Smashcima datasets ([smc/README.md](smc/README.md)).

We only work with solo staves, never grandstaves. Training uses the `solo26` architecture with `--input-subdivisions Staves`.


## Virtual environments

Two separate venvs, because the Zeus and Smashcima dependencies clash:

- `.venv-zeus`: Python 3.10 (TensorFlow), `zeus @ git+https://github.com/OmniOMR/zeus.git@v1.0.0`. It provides the `zeus` command (`musicorpus`, `render`, `pickle`, `train`, ...).
- `smc/.venv`: Python 3.11+ (Smashcima has problems on 3.10), `pip install -e smc`. It provides the `smc` command. It **cannot import zeus**, so it calls the same `lmx` functions that zeus uses instead.


## Related repositories and data (local clones)

| What | Local path | Upstream |
| --- | --- | --- |
| Zeus (OMR model, dataset format, CLI) | `~/ufal/zeus` | https://github.com/OmniOMR/zeus (we use tag `v1.0.0`) |
| LMX (linearized MusicXML, normalization, MuseScore rendering) | `~/ufal/lmx` | pinned to commit `87fca1c38bda83bc032596ab00af28412f92941d`, the same one zeus v1.0.0 uses |
| Smashcima (handwritten music synthesizer) | `~/ufal/Smashcima` | https://github.com/OMR-Research/Smashcima (we use `smashcima==1.1.2` from PyPI) |
| ICDAR 2026 paper repo (previous Smashcima experiments; source of the `smc` code) | `~/ufal/icdar26` | synthesis code in `app/datasets/smashcima`, Smashcima assets in `smashcima_assets/` |
| MuNG (music notation graph format, used by OmniOMR annotations) | `~/ufal/mung` | parsing code in `mung/`; `docs/annotation-instructions` and `docs/ontology-reference` explain the classes (e.g. the `numeralN` to `timeSigN` renaming) |
| MusiCorpus datasets (source of all Zeus datasets) | `~/musicorpus/` | `CVC.Dolores`, `UFAL.OmniOMR`, `UFAL.OlimpicSynthetic`, `UFAL.OlimpicScanned` |


## Datasets

| MusiCorpus source | `datasets/` folder | Solo-staff samples |
| --- | --- | --- |
| `CVC.Dolores` | `dolores` | 10,209 |
| `UFAL.OmniOMR` | `omniomr` | 1,170 |
| `UFAL.OlimpicSynthetic` | `olimpic-synthetic` | 26,364 |
| `UFAL.OlimpicScanned` | `olimpic-scanned` | (validation/test only) |

Smashcima variants are named `<dataset>-smc-<glyphs>`, with glyphs `gmpp` (MUSCIMA++), `gomni` (OmniOMR) or `gboth` (random per image). We synthesize 4 copies for OLiMPiC and 8 for Dolores and OmniOMR.

Zeus dataset format, briefly:

- `samples.{train,validation,test,all}.txt` list sample names like `samples/<page>/Staves_N`.
- Each sample has `.musicxml`, `.lmx` and image files (`.jpg`/`.png`).
- **Image suffix variants** are alternative images of the same sample, e.g. `_rendered.png` (MuseScore B/W) or `_copy1.jpg`, `_copy2.jpg`, ... (Smashcima copies with different seeds).
- `zeus pickle [--image-suffix X] [--benevolent] samples.split.txt` writes `samples[X].split.pickle`. `--benevolent` skips samples that are missing the image. Training takes the pickles.

The OmniOMR MusiCorpus `splits.json` has 60 train, 20 validation and 20 test pages. Each page folder has `transcription.mung` and `metadata.json` (with `dpi`).


## Smashcima synthesis (`smc`): things learned

- Smashcima renders only header clefs, noteheads, stems, beams, flags, rests, dots, sharp/flat/natural accidentals, ledger lines and barlines. It does **not** render key or time signatures, slurs, tuplets, grace notes, etc.
- Therefore `smc` removes all key and time signatures (including mid-staff changes) from the MusicXML and LMX using LMX normalization. Everything else Smashcima cannot draw is deliberately ignored: it stays in the annotation and is still rendered.
- The Smashcima image width comes from a MuseScore render of the modified MusicXML (`_rendered.png`, kept in the output for comparison), not from the original images.
- OmniOMR glyphs (bundle `OmniOmrIjdarGlyphs`, formerly called "mzk" glyphs in icdar26) are extracted from the OmniOMR **train split** pages only. This contaminates OmniOMR K-fold cross-validation, which is accepted.
- Smashcima's MUSCIMA++ download URL is dead, so copy the `MuscimaPP` and `MuscimaPPGlyphs` asset bundles from `~/ufal/icdar26/smashcima_assets`.
- Provenance of icdar26: its "mzk" glyphs came from a pre-release OmniOMR snapshot, cut into grandstaff crops and split over crops rather than pages, so they leaked across the current page splits. Its `dpi_values.csv` equals the `dpi` field of the MusiCorpus `metadata.json` files.
