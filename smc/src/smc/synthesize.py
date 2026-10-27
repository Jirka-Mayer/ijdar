import hashlib
import random
import shutil
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from lmx.musescore.MuseScore import MuseScore
from lmx.musescore.render_staff import render_staff
from lmx.musicxml.io.read_musicxml_tree_from_file import read_musicxml_tree_from_file

from .normalize_musicxml import normalize_musicxml_file
from .OmniOmrSoloStaffModel import OmniOmrSoloStaffModel
from .prepare_smashcima_input import prepare_smashcima_input_file
from .SamplesFile import Sample, SamplesFile
from .SoloStaffModel import NotationOverflowError, SoloStaffModel

GLYPH_SETS = ["mpp", "omniomr", "both"]

BATCH_SIZE = 100
"""How many samples to render by MuseScore at once"""

MUSESCORE_PAGE_WIDTH_TENTHS = 2_500
"""Same as the 'zeus render' default"""

MUSESCORE_RETRY_PAGE_WIDTH_TENTHS = 10_000
"""Samples that overflow the default page width are re-rendered
with this page width, so that we do not lose them"""

MUSESCORE_STAFF_HEIGHT_PX = 300 * 7 / 25.4
"""Staff height in MuseScore renders: 7mm (40 tenths) at 300 DPI"""


@dataclass
class SynthesisOptions:
    glyphs: str
    """Which glyphs to use: 'mpp', 'omniomr', or 'both' (random per image)"""

    copies: int
    """How many synthetic images to render for each sample
    (image suffixes _copy1, _copy2, ...)"""

    width_magic_factor: float
    """Multiplies the MuseScore notation width to get the
    Smashcima staff width"""

    output_height: int | None
    """Height of the output images in pixels, None for full resolution"""

    no_augmentation: bool
    """Disables Smashcima image-augmentation postprocessing"""

    seed: int
    """Global seed for the synthesis"""

    overwrite: bool
    """Re-render images that already exist (otherwise they are skipped)"""

    copy_original_images: bool
    """Copy the original image next to the synthetic ones (debugging)"""


def synthesize_samples(
        input_dataset: Path,
        output_dataset: Path,
        options: SynthesisOptions,
        slice_count: int,
        slice_index: int,
        debug_samples: int,
):
    """Synthesizes the smashcima variant of a zeus dataset"""
    assert options.glyphs in GLYPH_SETS
    assert options.copies >= 1
    assert slice_count > 0
    assert slice_index >= 0 and slice_index < slice_count

    # collect samples from all the split files (deduplicated and sorted)
    samples_files = sorted(input_dataset.glob("samples.*.txt"))
    assert len(samples_files) > 0, f"No samples files found in {input_dataset}"
    all_samples: dict[str, Sample] = {}
    for samples_file_path in samples_files:
        for sample in SamplesFile.load(samples_file_path):
            all_samples[sample.name] = sample
    samples = sorted(all_samples.values(), key=lambda s: s.name)

    # perform a fixed shuffle to distribute sample
    # difficulty among slices more evenly
    random.Random(42).shuffle(samples)

    if debug_samples > 0:
        slice_samples = samples[:debug_samples]
        print(f"Debugging with {len(slice_samples)} samples...")
    else:
        slice_samples = samples[slice_index::slice_count]
        print(f"There are {len(samples)} samples in the input dataset.")
        print(f"This process works with slice {slice_index} out of {slice_count}.")
        print(f"This slice has {len(slice_samples)} samples.")
    print(f"Glyphs: {options.glyphs}, copies: {options.copies}, seed: {options.seed}")
    print("")

    # copy samples files to the output dataset
    # (only the first slice does it, to not have multiple writers)
    output_dataset.mkdir(parents=True, exist_ok=True)
    if slice_index == 0:
        for samples_file_path in samples_files:
            shutil.copyfile(samples_file_path, output_dataset / samples_file_path.name)

    # set up MuseScore (from the 'musescore/' folder in the working directory)
    ms = MuseScore.resolve_linux_default()

    # set up smashcima models
    models: dict[str, SoloStaffModel] = {}
    if options.glyphs in ["mpp", "both"]:
        models["mpp"] = SoloStaffModel(options.width_magic_factor)
    if options.glyphs in ["omniomr", "both"]:
        models["omniomr"] = OmniOmrSoloStaffModel(options.width_magic_factor)

    # go through the samples in batches
    stats: dict[str, int] = {}
    for batch_start in range(0, len(slice_samples), BATCH_SIZE):
        batch = [
            (
                input_sample,
                Sample(
                    name=input_sample.name,
                    path=output_dataset / input_sample.name
                )
            )
            for input_sample in slice_samples[batch_start:batch_start + BATCH_SIZE]
        ]

        # normalize MusicXML (remove key and time signatures) and write LMX
        normalized_batch: list[tuple[Sample, Sample]] = []
        for input_sample, output_sample in batch:
            output_sample.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                normalize_musicxml_file(
                    input_musicxml_path=input_sample.file(".musicxml"),
                    output_musicxml_path=output_sample.file(".musicxml"),
                    output_lmx_path=output_sample.file(".lmx"),
                )
                normalized_batch.append((input_sample, output_sample))
            except Exception:
                print(f"Error normalizing MusicXML of {input_sample.name}: ", end="")
                traceback.print_exc()
                stats["normalization-error"] = \
                    stats.get("normalization-error", 0) + options.copies

        # render the normalized MusicXML with MuseScore
        render_with_musescore(
            ms=ms,
            output_samples=[o for _, o in normalized_batch],
            overwrite=options.overwrite,
        )

        # render smashcima copies
        for i, (input_sample, output_sample) in enumerate(normalized_batch):
            print(
                f"{batch_start+i+1}/{len(slice_samples)} | {input_sample.name}",
                flush=True
            )
            outcomes = synthesize_one_sample(
                input_sample=input_sample,
                output_sample=output_sample,
                models=models,
                options=options,
            )
            for outcome in outcomes:
                stats[outcome] = stats.get(outcome, 0) + 1

    print("")
    print("Outcome counts (per image):", stats)


def render_with_musescore(
        ms: MuseScore,
        output_samples: list[Sample],
        overwrite: bool,
):
    """Renders samples into the '_rendered.png' images via MuseScore,
    the same way as the 'zeus render' command does it"""
    to_render = [
        s for s in output_samples
        if overwrite or not s.file("_rendered.png").exists()
    ]
    if len(to_render) == 0:
        return

    for s in to_render:
        s.file("_rendered.png").unlink(missing_ok=True)

    for page_width_tenths in [
        MUSESCORE_PAGE_WIDTH_TENTHS,
        MUSESCORE_RETRY_PAGE_WIDTH_TENTHS
    ]:
        overflown_sample_indices: list[int] = []
        render_staff(
            ms=ms,
            part_element=[_load_part(s.file(".musicxml")) for s in to_render],
            output_png_file=[s.file("_rendered.png") for s in to_render],
            render_invisible_attributes=False,
            page_width_tenths=page_width_tenths,
            on_page_overflow="return-index",
            overflown_sample_indices=overflown_sample_indices,
        )
        to_render = [to_render[i] for i in overflown_sample_indices]
        for s in to_render:
            print(f"MuseScore page overflow at {page_width_tenths} tenths:", s.name)
        if len(to_render) == 0:
            break


def _load_part(musicxml_path: Path):
    parts = read_musicxml_tree_from_file(musicxml_path).findall("part")
    assert len(parts) == 1
    return parts[0]


def measure_notation_width(rendered_image_path: Path) -> float:
    """Returns the width of the notation in a MuseScore render
    in staff heights (measured from ink, since the render is trimmed
    with some padding around the content)"""
    img = cv2.imread(str(rendered_image_path), cv2.IMREAD_GRAYSCALE)
    assert img is not None
    ink_columns = np.where((img < 128).any(axis=0))[0]
    return (ink_columns.max() - ink_columns.min() + 1) / MUSESCORE_STAFF_HEIGHT_PX


def synthesize_one_sample(
        input_sample: Sample,
        output_sample: Sample,
        models: dict[str, SoloStaffModel],
        options: SynthesisOptions,
) -> list[str]:
    """Renders all the smashcima copies of a sample (whose MusicXML has
    already been normalized and rendered by MuseScore).
    Returns outcomes for each copy (for statistics)."""

    if options.copy_original_images:
        original_image_path = input_sample.file(".jpg")
        if not original_image_path.exists():
            original_image_path = input_sample.file(".png")
        shutil.copyfile(
            original_image_path,
            output_sample.file("_original" + original_image_path.suffix)
        )

    # the width of the MuseScore render dictates the Smashcima image width
    if not output_sample.file("_rendered.png").exists():
        return ["musescore-overflow"] * options.copies
    notation_width = measure_notation_width(output_sample.file("_rendered.png"))

    # render individual copies
    outcomes: list[str] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        smashcima_input_path = Path(tmpdir) / "input.musicxml"
        prepare_smashcima_input_file(
            output_sample.file(".musicxml"),
            smashcima_input_path
        )

        for copy_number in range(1, options.copies + 1):
            image_path = output_sample.file(f"_copy{copy_number}.jpg")
            if image_path.exists() and not options.overwrite:
                outcomes.append("skipped-existing")
                continue

            # seed of this copy
            # NOTE: built-in hash() function is not stable across python sessions
            # so we use hashlib instead
            copy_seed = int(hashlib.sha1(
                f"{input_sample.name}|copy{copy_number}|{options.seed}".encode("utf-8")
            ).hexdigest(), 16) % (2 ** 64)

            # pick glyphs for this copy
            if options.glyphs == "both":
                glyphs = random.Random(copy_seed).choice(["mpp", "omniomr"])
            else:
                glyphs = options.glyphs

            try:
                bitmap = models[glyphs](
                    file=smashcima_input_path,
                    notation_width=notation_width,
                    sample_seed=copy_seed,
                    output_height=options.output_height,
                    no_augmentation=options.no_augmentation,
                )
            except NotationOverflowError as e:
                print(f"Copy {copy_number} [{glyphs}] overflows:", e)
                outcomes.append("overflow")
                continue
            except Exception:
                print(f"Copy {copy_number} [{glyphs}] error: ", end="")
                traceback.print_exc()
                outcomes.append("synthesis-error")
                continue

            print(f"Copy {copy_number} [{glyphs}] ok")
            image_path.unlink(missing_ok=True)
            cv2.imwrite(str(image_path), bitmap)
            outcomes.append("ok")

    return outcomes
