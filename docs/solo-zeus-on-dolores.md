# Solo Zeus on Dolores

Experiment name is `zod` = zeus on dolores.


## Table to fill

Each value is LMX-SER on OmniOMR staff-level test split.

| Ex. Name      | B/W | Smashcima | Authentic | SER    | SER FT |
| ------------- | --- | --------- | --------- | ------ | ------ |
| `zod-auth`    | ❌  | ❌        | ✅        |        |        |
| `zod-bw`      | ✅  | ❌        | ❌        |        |        |
| `zod-bw-auth` | ✅  | ❌        | ✅        | 42.421 | 39.337 |


## Preparing data

The experiment data sits in the `datasets/` folder, specifically the `dolores` and `omniomr` dataset. For both, all three splits are needed (train, validation, test).

See [prepare datasets](prepare-datasets.md) to get the relevant datasets ready.

After preparation, copy the relevant pickles to the compute cluster.


## Training models

On Dolores, we will train on both the `train` and `test` splits, which gives us 6294 + 2357 = 8651 samples. The `validation` split will be used for validation.

The 2024 olimpic zeus was trained for 500 epochs on a dataset of 15014 samples, which is 7507000 training samples. Since now our dataset has 8651 samples, depending on how many image variants we include in training, we will train for the following number of epochs:

| Image variants | Ideal epoch count | Used epoch count |
| -------------- | ----------------- | ---------------- |
| 1              | 867.7             | 870              |
| 2              | 433.8             | 430              |
| 3              | 289.2             | 290              |

```bash
zeus train \
    --experiment zod-bw-auth \
    --architecture solo26 \
    --input-subdivisions Staves \
    --train \
        datasets/dolores/samples_rendered.train.pickle \
        datasets/dolores/samples_rendered.test.pickle \
        datasets/dolores/samples.train.pickle \
        datasets/dolores/samples.test.pickle \
    --augment "h:8,rotate:1,v:4,de,en3:0.2,n:0.01,c:-1:1,b:-0.5:0.2" \
    --dev \
        datasets/dolores/samples_rendered.validation.pickle \
        datasets/dolores/samples.validation.pickle \
    --test \
        datasets/omniomr/samples_rendered.test.pickle \
        datasets/omniomr/samples.test.pickle \
    --epochs 430 \
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
        datasets/dolores/samples_rendered.train.pickle \
        datasets/dolores/samples_rendered.test.pickle \
        datasets/dolores/samples.train.pickle \
        datasets/dolores/samples.test.pickle \
    --augment "h:8,rotate:1,v:4,de,en3:0.2,n:0.01,c:-1:1,b:-0.5:0.2" \
    --batch-size 32
```