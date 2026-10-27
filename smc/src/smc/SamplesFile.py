from dataclasses import dataclass
from pathlib import Path


@dataclass
class Sample:
    """One sample from a samples file"""

    name: str
    """The exact string that is in the samples file on one line,
    e.g. 'samples/4904021-p1/Staves_2a'"""

    path: Path
    """
    Path to the sample, without file type suffix.

    The ".jpg" or "_copy1.jpg" or ".lmx" must be added
    to actually point to a file.
    """

    def file(self, suffix: str) -> Path:
        """Returns path to a sample file, e.g. file('_copy1.jpg')"""
        return self.path.with_name(self.path.name + suffix)


class SamplesFile:
    """Represents a samples file for a dataset, e.g. 'samples.train.txt'"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.samples: list[Sample] = []

    def append(self, sample_name: str) -> Sample:
        sample = Sample(
            name=sample_name,
            path=self.file_path.parent / sample_name
        )
        self.samples.append(sample)
        return sample

    def __len__(self) -> int:
        return len(self.samples)

    def __iter__(self):
        yield from self.samples

    def write(self):
        with open(self.file_path, "w") as f:
            for sample in self.samples:
                f.write(sample.name + "\n")

    @staticmethod
    def load(file_path: Path) -> "SamplesFile":
        samples_file = SamplesFile(file_path)
        with open(file_path, "r") as f:
            for line in f:
                if line.strip() != "":
                    samples_file.append(line.strip())
        return samples_file
