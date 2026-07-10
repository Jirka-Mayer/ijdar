# IJDAR Experiments

Here I run/track/code experiments for my final PhD Thesis journal paper (likely IJDAR).


## Setting up Zeus venv

```bash
python3.10 -m venv .venv-zeus
.venv-zeus/bin/pip install zeus @ git+https://github.com/OmniOMR/zeus.git@main
```

To update to latest zeus, do:

```bash
.venv-zeus/bin/pip uninstall zeus
.venv-zeus/bin/pip install zeus @ git+https://github.com/OmniOMR/zeus.git@main
```

You can also install via symlink on your laptop:

```bash
.venv-zeus/bin/pip install -e ../zeus
```

Now you can use the `zeus` command:

```bash
.venv-zeus/bin/zeus --help

# OR
source .venv-zeus/bin/activate
zeus --help
```


## Experiments


### Solo Zeus on Dolores

Before we can start picking apart which parts of data synthesis affect results how, we should put Smashcima synthesis in the context of other synthesis (e.g. MuseScore B/W images). We still live in the pre-training, then fine-tuning regime. We pre-train on Dolores, then fine-tune on OmniOMR. OmniOMR test set is the ultimate goal.

We pre-train on Dolores train split with these image variants:

- B/W rendered from MuseScore
- Smashcima synthetic
- Authentic scanned images

And we train on all, as well as on ablated subsets to see the effect of each.

[Learn more about this experiment here](solo-zeus-on-dolores.md)
