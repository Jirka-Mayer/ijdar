import argparse
import sys
from pathlib import Path

from .config import SMASHCIMA_ASSETS_PATH


def main():
    parser = argparse.ArgumentParser(
        prog="smc",
        description="Smashcima data generation for 'smc' models"
    )
    subparsers = parser.add_subparsers(title="available commands", dest="command")

    # === install-assets ===

    install_parser = subparsers.add_parser(
        "install-assets",
        description=
            "Installs all smashcima asset bundles (MUSCIMA++ glyphs and "
            "OmniOMR glyphs). Run this once before running parallel "
            "synthesis, so that the processes do not install concurrently."
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Re-install the OmniOMR glyphs bundle even if already installed"
    )
    install_parser.add_argument(
        "--debug-folder",
        type=Path,
        default=None,
        help="Dump all extracted OmniOMR glyphs as images into this folder"
    )

    # === synthesize ===

    synthesize_parser = subparsers.add_parser(
        "synthesize",
        description=
            "Creates the smashcima variant of a zeus dataset. Key and time "
            "signatures are removed from the MusicXML and LMX, and each "
            "sample is rendered into images with suffixes _copy1, _copy2, ..."
    )
    synthesize_parser.add_argument(
        "--input-dataset",
        required=True,
        type=Path,
        help="Path to the input zeus dataset folder with the samples.*.txt files"
    )
    synthesize_parser.add_argument(
        "--output-dataset",
        required=True,
        type=Path,
        help="Path to the output zeus dataset folder"
    )
    synthesize_parser.add_argument(
        "--glyphs",
        required=True,
        choices=["mpp", "omniomr", "both"],
        help=
            "Which glyphs to use: MUSCIMA++, OmniOMR (train split), "
            "or both (randomly chosen for each image)"
    )
    synthesize_parser.add_argument(
        "--copies",
        required=True,
        type=int,
        help=
            "How many images to render for each sample (_copy1 to _copyN). "
            "Already existing images are skipped, so this number can be "
            "increased later to just add more copies."
    )
    synthesize_parser.add_argument(
        "--width-magic-factor",
        type=float,
        default=1.0,
        help=
            "How to multiply the width of the MuseScore-engraved notation "
            "to get the width of the Smashcima staff (default 1.0)."
    )
    synthesize_parser.add_argument(
        "--output-height",
        type=int,
        default=192,
        help="Height of the output images in pixels, 0 for full resolution"
    )
    synthesize_parser.add_argument(
        "--no-augmentation",
        action="store_true",
        help="Disables Smashcima image-augmentation postprocessing"
    )
    synthesize_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Global seed for the synthesizer"
    )
    synthesize_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-render images that already exist"
    )
    synthesize_parser.add_argument(
        "--copy-original-images",
        action="store_true",
        help="Copy original images next to the synthetic ones (for debugging)"
    )
    synthesize_parser.add_argument(
        "--slice-count",
        type=int,
        default=1,
        help="In between how many slices (processes) is the task split"
    )
    synthesize_parser.add_argument(
        "--slice-index",
        type=int,
        default=0,
        help="What slice should this process compute"
    )
    synthesize_parser.add_argument(
        "--debug-samples",
        type=int,
        default=0,
        help=
            "Process only this many samples (taken from the start of the "
            "shuffled sample list) to debug the synthesis. 0 means all."
    )

    args = parser.parse_args()

    if args.command == "install-assets":
        install_assets(force=args.force, debug_folder=args.debug_folder)

    elif args.command == "synthesize":
        from .synthesize import SynthesisOptions, synthesize_samples
        synthesize_samples(
            input_dataset=args.input_dataset,
            output_dataset=args.output_dataset,
            options=SynthesisOptions(
                glyphs=args.glyphs,
                copies=args.copies,
                width_magic_factor=args.width_magic_factor,
                output_height=args.output_height or None,
                no_augmentation=args.no_augmentation,
                seed=args.seed,
                overwrite=args.overwrite,
                copy_original_images=args.copy_original_images,
            ),
            slice_count=args.slice_count,
            slice_index=args.slice_index,
            debug_samples=args.debug_samples,
        )

    else:
        parser.print_help()
        sys.exit(2)


def install_assets(force: bool, debug_folder: Path | None):
    from smashcima.assets.AssetRepository import AssetRepository

    from .omniomr_glyphs.OmniOmrIjdarGlyphs import OmniOmrIjdarGlyphs
    from .OmniOmrSoloStaffModel import OmniOmrSoloStaffModel
    from .SoloStaffModel import SoloStaffModel

    print("Smashcima assets folder:", SMASHCIMA_ASSETS_PATH)
    repository = AssetRepository(SMASHCIMA_ASSETS_PATH)
    bundle = repository.resolve_bundle(OmniOmrIjdarGlyphs, force_install=force)

    # constructing the models resolves (installs) all the bundles they need
    SoloStaffModel(width_magic_factor=1.0)
    OmniOmrSoloStaffModel(width_magic_factor=1.0)

    if debug_folder is not None:
        print("Building the debug folder...")
        bundle.build_debug_folder(debug_folder)

    print("Done.")
