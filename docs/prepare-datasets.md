# Prepare datasets

These are code snippets that prepare the Zeus datasets used for training (pickles) from MusiCorpus dataset located at `~/musicorpus`.

We only work with solo-staff data, no grandstaves.

How datasets are named before and after preparation:

| MusiCorpus Source | Local `datasets` folder name |
| --- | --- |
| `CVC.Dolores` | `dolores` |
| `UFAL.OmniOMR` | `omniomr` |
| `UFAL.OlimpicSynthetic` | `olimpic-synthetic` |
| `UFAL.OlimpicScanned` | `olimpic-scanned` |


## Dolores

```bash
zeus musicorpus \
    --input ~/musicorpus/CVC.Dolores \
    --output datasets/dolores \
    --take-staves
zeus render \
    --image-suffix '_rendered' \
    datasets/dolores/samples.all.txt
zeus pickle datasets/dolores/samples.train.txt
zeus pickle datasets/dolores/samples.test.txt
zeus pickle datasets/dolores/samples.validation.txt
zeus pickle --image-suffix '_rendered' --benevolent datasets/dolores/samples.train.txt
zeus pickle --image-suffix '_rendered' --benevolent datasets/dolores/samples.test.txt
zeus pickle --image-suffix '_rendered' --benevolent datasets/dolores/samples.validation.txt
```


## OmniOMR

```bash
zeus musicorpus \
    --input ~/musicorpus/UFAL.OmniOMR \
    --output datasets/omniomr \
    --take-staves
zeus render \
    --image-suffix '_rendered' \
    datasets/omniomr/samples.all.txt
zeus pickle datasets/omniomr/samples.train.txt
zeus pickle datasets/omniomr/samples.test.txt
zeus pickle datasets/omniomr/samples.validation.txt
zeus pickle --image-suffix '_rendered' --benevolent datasets/omniomr/samples.train.txt
zeus pickle --image-suffix '_rendered' --benevolent datasets/omniomr/samples.test.txt
zeus pickle --image-suffix '_rendered' --benevolent datasets/omniomr/samples.validation.txt
```


## OLiMPiC Scanned

```bash
zeus musicorpus \
    --input ~/musicorpus/UFAL.OlimpicScanned \
    --output datasets/olimpic-scanned \
    --take-staves
zeus pickle datasets/olimpic-scanned/samples.test.txt
zeus pickle datasets/olimpic-scanned/samples.validation.txt
```


## OLiMPiC Synthetic

```bash
zeus musicorpus \
    --input ~/musicorpus/UFAL.OlimpicSynthetic \
    --output datasets/olimpic-synthetic \
    --take-staves
zeus pickle datasets/olimpic-synthetic/samples.train.txt
zeus pickle datasets/olimpic-synthetic/samples.test.txt
zeus pickle datasets/olimpic-synthetic/samples.validation.txt
```


## Smashcima setup

The Smashcima datasets are synthesized by the `smc` package, which has its own virtual environment (see `smc/README.md` for details). Set it up once, from the repository root:

```bash
python3 -m venv smc/.venv
smc/.venv/bin/pip install -e smc

# The MUSCIMA++ download URL in Smashcima is dead, so copy the bundles
# from an existing installation first (or the whole smc/smashcima_assets folder)
mkdir -p smc/smashcima_assets
cp -r ~/ufal/icdar26/smashcima_assets/MuscimaPP smc/smashcima_assets/
cp -r ~/ufal/icdar26/smashcima_assets/MuscimaPPGlyphs smc/smashcima_assets/

# downloads the rest and extracts OmniOMR glyphs from ~/musicorpus/UFAL.OmniOMR (train split)
smc/.venv/bin/smc install-assets
```

Each Smashcima dataset is synthesized from an existing solo-staff dataset (which must contain the musicxml files) in three glyph variants (`gmpp` = MUSCIMA++, `gomni` = OmniOMR, `gboth` = random per image). Key and time signatures are removed from the annotations. Each sample is rendered in N copies with image suffixes `_copy1`, `_copy2`, ..., which are pickled separately. The `_rendered` images contain the same (modified) music engraved by MuseScore, for comparison.

The synthesis runs on the cluster, from the head node in the repository root (use tmux/screen). Samples that fail to synthesize have no image, hence the `--benevolent` pickling.


## OLiMPiC Smashcima

These commands create these datasets:

```
datasets/olimpic-smc-gmpp
datasets/olimpic-smc-gomni
datasets/olimpic-smc-gboth
```

Requirements: `olimpic-synthetic` must be present with musicxml files.

```bash
bash smc/synthesize-on-cluster.sh datasets/olimpic-synthetic datasets/olimpic-smc-gmpp mpp 4
bash smc/synthesize-on-cluster.sh datasets/olimpic-synthetic datasets/olimpic-smc-gomni omniomr 4
bash smc/synthesize-on-cluster.sh datasets/olimpic-synthetic datasets/olimpic-smc-gboth both 4

for glyphs in gmpp gomni gboth; do
    for copy in 1 2 3 4; do
        for split in train test validation; do
            zeus pickle --image-suffix "_copy$copy" --benevolent \
                datasets/olimpic-smc-$glyphs/samples.$split.txt
        done
    done
done
```


## Dolores Smashcima

These commands create these datasets:

```
datasets/dolores-smc-gmpp
datasets/dolores-smc-gomni
datasets/dolores-smc-gboth
```

Requirements: `dolores` must be present with musicxml files.

```bash
bash smc/synthesize-on-cluster.sh datasets/dolores datasets/dolores-smc-gmpp mpp 8
bash smc/synthesize-on-cluster.sh datasets/dolores datasets/dolores-smc-gomni omniomr 8
bash smc/synthesize-on-cluster.sh datasets/dolores datasets/dolores-smc-gboth both 8

for glyphs in gmpp gomni gboth; do
    for copy in 1 2 3 4 5 6 7 8; do
        for split in train test validation; do
            zeus pickle --image-suffix "_copy$copy" --benevolent \
                datasets/dolores-smc-$glyphs/samples.$split.txt
        done
    done
done
```


## OmniOMR Smashcima

Not used in the experiments, prepared just for completeness. Note that the OmniOMR glyphs come from the OmniOMR train split, so the `gomni` and `gboth` variants leak glyph shapes into the OmniOMR validation and test splits.

These commands create these datasets:

```
datasets/omniomr-smc-gmpp
datasets/omniomr-smc-gomni
datasets/omniomr-smc-gboth
```

Requirements: `omniomr` must be present with musicxml files.

```bash
bash smc/synthesize-on-cluster.sh datasets/omniomr datasets/omniomr-smc-gmpp mpp 8
bash smc/synthesize-on-cluster.sh datasets/omniomr datasets/omniomr-smc-gomni omniomr 8
bash smc/synthesize-on-cluster.sh datasets/omniomr datasets/omniomr-smc-gboth both 8

for glyphs in gmpp gomni gboth; do
    for copy in 1 2 3 4 5 6 7 8; do
        for split in train test validation; do
            zeus pickle --image-suffix "_copy$copy" --benevolent \
                datasets/omniomr-smc-$glyphs/samples.$split.txt
        done
    done
done
```
