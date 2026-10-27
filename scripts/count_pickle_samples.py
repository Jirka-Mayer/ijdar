"""
Counts samples in zeus dataset pickles and compares them with the samples.txt
files they were made from, to see how many samples 'zeus pickle --benevolent'
skipped. Also sums the pickles up and computes the epoch count for the
7507000 training samples budget (see docs/smashcima.md).

Run with the zeus venv, passing the pickles of one training mix:

    .venv-zeus/bin/python scripts/count_pickle_samples.py \
        datasets/dolores/samples.train.pickle \
        datasets/dolores-smc-gboth/samples_copy1.train.pickle
"""

import argparse
import math
from pathlib import Path

from zeus.data.samples_file import SamplesFile
from zeus.data.zeus_dataset import ZeusDataset

TRAINING_SAMPLES_BUDGET = 7_507_000


def samples_file_path_for_pickle(pickle_path: Path) -> Path:
    """Inverse of the zeus pickle naming,
    e.g. samples_copy1.train.pickle -> samples.train.txt"""
    stem_parts = pickle_path.stem.split(".")
    stem_parts[0] = "samples"
    return pickle_path.with_name(".".join(stem_parts) + ".txt")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("pickles", nargs="+", type=Path)
    args = parser.parse_args()

    total = 0
    for pickle_path in args.pickles:
        pickle_count = len(ZeusDataset.load_from_pickle_file(pickle_path).samples)
        txt_count = len(SamplesFile.load(samples_file_path_for_pickle(pickle_path)))
        discarded = txt_count - pickle_count
        total += pickle_count
        print(
            f"{pickle_count:>7} / {txt_count:>7} "
            f"(discarded {discarded:>5}, {discarded / txt_count:6.2%})  "
            f"{pickle_path}",
            flush=True
        )

    print()
    print(f"samples in epoch: {total}")
    print(f"epochs = ceil({TRAINING_SAMPLES_BUDGET} / {total}) "
          f"= {math.ceil(TRAINING_SAMPLES_BUDGET / total)}")


if __name__ == "__main__":
    main()
