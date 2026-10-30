# IJDAR Experiments

Here I run/track/code experiments for my final PhD Thesis journal paper (likely IJDAR).


## Setting up Zeus venv

```bash
python3.10 -m venv .venv-zeus
.venv-zeus/bin/pip install 'zeus @ git+https://github.com/OmniOMR/zeus.git@v1.1.0'
```

Now you can use the `zeus` command:

```bash
.venv-zeus/bin/zeus --help

# OR
source .venv-zeus/bin/activate
zeus --help
```


## Running GPU interactive job on LRC

```bash
srun --pty --gpus=1 --mem=32G -p gpu-ms,gpu-troja --constraint="gpuram48G|gpuram24G" bash

module load cuda/11.8-cudnn8.6

zeus train \
    ...
```


## Experiments


### Smascima - Experiments measuring smashcima data effect on Zeus

We train a `solo26` Zeus on progressively more smashcima samples to see how it can attack the OmniOMR dataset when fine-tuned. Similar as in ICDAR 2026, just now doing a grid-search instead of computing one number. And also using Dolores now.

[Learn more about this experiment here](docs/smashcima.md)


### AYCE - All you can eat

We take all the data we have and train a `solo26` Zeus on it to see how low we can get the SER on the OmniOMR test set.

[Learn more about this experiment here](docs/ayce.md)


### Solo Zeus on Dolores

Before we can start picking apart which parts of data synthesis affect results how, we should put Smashcima synthesis in the context of other synthesis (e.g. MuseScore B/W images). We still live in the pre-training, then fine-tuning regime. We pre-train on Dolores, then fine-tune on OmniOMR. OmniOMR test set is the ultimate goal.

We pre-train on Dolores train split with these image variants:

- B/W rendered from MuseScore
- Smashcima synthetic
- Authentic scanned images

And we train on all, as well as on ablated subsets to see the effect of each.

[Learn more about this experiment here](docs/solo-zeus-on-dolores.md)
