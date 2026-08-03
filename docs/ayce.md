# AYCE - All you can eat experiment

Experiment name is `ayce` = all you can eat.

We follow results from the `zod` experiments, where we found that Dolores provides a good baseline for image style when it comes to OmniOMR as the target, however, it does not have the necessary musical complexity so the language model suffers on OmniOMR - it has 40% SER even on the B/W rendered test set (and about the same on the original scanned). This means the visual appearance is not the issue, the content is. So the main fix is to include the OLiMPiC musical data, which is much more interesting music-wise. And while we do that, we'll also include the scanned data, because why not.


## Preparing data

The experiment data sits in the `datasets/` folder. These are the datasets we use for training:

- All of Dolores, except `test`
    - `dolores/samples.train.pickle`
    - `dolores/samples.validation.pickle`
    - `dolores/samples_rendered.train.pickle`
    - `dolores/samples_rendered.validation.pickle`
- OLiMPiC synthetic, `train` only
    - `olimpic-synthetic/samples.train.pickle`
- OLiMPiC scanned, `validation` only
    - `olimpic-scanned/samples.validation.pickle`
- OmniOMR, `train` only
    - `omniomr/samples.train.pickle`
    - `omniomr/samples_rendered.train.pickle`

We will do validation on:

- `omniomr/samples.validation.pickle`
- `omniomr/samples_rendered.validation.pickle`

And final evalutaion on:

- `omniomr/samples.test.pickle`
- `omniomr/samples_rendered.test.pickle`
- `dolores/samples.test.pickle`
- `dolores/samples_rendered.test.pickle`
- `olimpic-scanned/samples.test.pickle`
- `olimpic-synthetic/samples.test.pickle`

See [prepare datasets](prepare-datasets.md) to get the relevant datasets ready.

After preparation, copy the relevant pickles to the compute cluster.


## Training models

Let's count samples in one epoch:

- Scanned images (10899 samples)
    - Dolores = 6294 + 1558 = 7852
    - Olimpic scanned validation = 2352
    - OmniOMR train = 695
- MuseScore images (32049 samples)
    - Dolores rendered ~= 7852
    - (forgot to count omniomr rendered, not that it would make a difference)
    - Olimpic synthetic train = 24197

Total 42948 training samples in one epoch.

I fear the OmniOMR train will be really undersampled. But hopefully the resulting language model will be storng enough, that a fine-tuning on OmniOMR train will help afterwards. We will se.

The 2024 olimpic zeus was trained for 500 epochs on a dataset of 15014 samples, which is 7507000 training samples. Since now our dataset has 42948 samples, we need to train for 174.8 epochs to get the same training time.

Let's train at 200 epochs and see what happens. Let's also train `ayce-long` for 600 epochs.

```bash
zeus train \
    --experiment ayce \
    --architecture solo26 \
    --input-subdivisions Staves \
    --train \
        datasets/dolores/samples.train.pickle \
        datasets/dolores/samples.validation.pickle \
        datasets/dolores/samples_rendered.train.pickle \
        datasets/dolores/samples_rendered.validation.pickle \
        datasets/olimpic-synthetic/samples.train.pickle \
        datasets/olimpic-scanned/samples.validation.pickle \
        datasets/omniomr/samples.train.pickle \
        datasets/omniomr/samples_rendered.train.pickle \
    --augment "h:8,rotate:1,v:4,de,en3:0.2,n:0.01,c:-1:1,b:-0.5:0.2" \
    --dev \
        datasets/omniomr/samples.validation.pickle \
        datasets/omniomr/samples_rendered.validation.pickle \
    --test \
        datasets/omniomr/samples.test.pickle \
        datasets/omniomr/samples_rendered.test.pickle \
        datasets/dolores/samples.test.pickle \
        datasets/dolores/samples_rendered.test.pickle \
        datasets/olimpic-scanned/samples.test.pickle \
        datasets/olimpic-synthetic/samples.test.pickle \
    --epochs 200 \
    --evaluation-from 10 \
    --evaluation-each 10 \
    --batch-size 32 \
    --learning-rate 1e-3 \
    --lr-decay cos \
    --quiet-tf
```

```bash
zeus visualize-data \
    --architecture solo26 \
    --train \
        datasets/dolores/samples.train.pickle \
        datasets/dolores/samples.validation.pickle \
        datasets/dolores/samples_rendered.train.pickle \
        datasets/dolores/samples_rendered.validation.pickle \
        datasets/olimpic-synthetic/samples.train.pickle \
        datasets/olimpic-scanned/samples.validation.pickle \
        datasets/omniomr/samples.train.pickle \
        datasets/omniomr/samples_rendered.train.pickle \
    --augment "h:8,rotate:1,v:4,de,en3:0.2,n:0.01,c:-1:1,b:-0.5:0.2" \
    --batch-size 32
```
