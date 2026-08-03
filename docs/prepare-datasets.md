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
