import json
import os
import pickle
import shutil
import traceback
from pathlib import Path

import cv2
from smashcima.assets.AssetBundle import AssetBundle
from smashcima.assets.glyphs.mung.extraction.ExtractedBag import ExtractedBag
from smashcima.assets.glyphs.mung.extraction.MungDocument import MungDocument
from smashcima.assets.glyphs.mung.MungGlyphMetadata import MungGlyphMetadata
from smashcima.assets.glyphs.mung.repository.MungSymbolRepository import MungSymbolRepository
from smashcima.exporting.DebugGlyphRenderer import DebugGlyphRenderer
from tqdm import tqdm

from .OmniOmrIjdarSymbolExtractor import OmniOmrIjdarSymbolExtractor

OMNIOMR_MUSICORPUS_PATH = Path(
    os.environ.get("SMC_OMNIOMR_MUSICORPUS", "~/musicorpus/UFAL.OmniOMR")
).expanduser()
"""Path to the OmniOMR dataset in the MusiCorpus format,
can be overriden by the SMC_OMNIOMR_MUSICORPUS env variable"""

GLYPHS_SPLIT = "train"
"""Glyphs are extracted only from pages of this split, to prevent
data contamination with the validation and test splits"""


class OmniOmrIjdarGlyphs(AssetBundle):
    """
    Glyphs extracted from the page-level MuNG annotations
    of the train split of the OmniOMR dataset (the MusiCorpus release).
    """

    def __post_init__(self) -> None:
        self._symbol_repository_cache: MungSymbolRepository | None = None

    @property
    def symbol_repository_path(self) -> Path:
        return self.bundle_directory / "symbol_repository.pkl"

    def page_paths(self) -> list[Path]:
        """Returns paths to musicorpus page folders to extract glyphs from"""
        with open(OMNIOMR_MUSICORPUS_PATH / "splits.json", "r") as f:
            splits = json.load(f)
        return [
            OMNIOMR_MUSICORPUS_PATH / page_name
            for page_name in sorted(splits[GLYPHS_SPLIT])
        ]

    def install(self) -> None:
        """Extracts data from the MuNG files and bundles it up
        in the symbol repository in a pickle file."""
        page_paths = self.page_paths()
        print(
            f"Extracting glyphs from {len(page_paths)} pages "
            f"of the '{GLYPHS_SPLIT}' split of {OMNIOMR_MUSICORPUS_PATH}"
        )

        # collects extracted symbols
        bag = ExtractedBag()

        # go through all the MuNG XML files
        for page_path in tqdm(page_paths):
            with open(page_path / "metadata.json", "r") as f:
                dpi = float(json.load(f)["dpi"])
            document = MungDocument.load(
                page_path / "transcription.mung",
                dpi=dpi
            )

            try:
                extractor = OmniOmrIjdarSymbolExtractor(document=document, bag=bag)
                extractor.extract_all_symbols()
            except Exception:
                print(page_path.name, "@", dpi)
                print(traceback.format_exc())

        # build the repository
        repository = bag.build_symbol_repository()

        # dump the repository into a pickle file
        with open(self.symbol_repository_path, "wb") as file:
            pickle.dump(repository, file)
            print("Writing...", self.symbol_repository_path)

    def load_symbol_repository(self) -> MungSymbolRepository:
        """Loads the symbol repository from its pickle file"""
        if self._symbol_repository_cache is None:
            with open(self.symbol_repository_path, "rb") as file:
                repository = pickle.load(file)
            assert isinstance(repository, MungSymbolRepository)
            self._symbol_repository_cache = repository

        return self._symbol_repository_cache

    def build_debug_folder(self, debug_folder: Path):
        """Dumps all the extracted glyphs into a debug folder
        for visual inspection."""
        repository = self.load_symbol_repository()

        shutil.rmtree(debug_folder, ignore_errors=True)
        debug_folder.mkdir(parents=True)

        def _iter_label_pgs():
            for label, pgs in repository.glyphs_index.glyphs_by_label.items():
                yield label, pgs
            for label, pgls in repository.line_glyphs_index.glyphs_by_label.items():
                yield label, pgls.lines

        glyph_renderer = DebugGlyphRenderer()
        for label, packed_glyphs in _iter_label_pgs():
            glyphs_folder = debug_folder / label.replace(":", "-")
            glyphs_folder.mkdir()

            print(label, "...")
            for packed_glyph in tqdm(packed_glyphs):
                glyph = packed_glyph.unpack()
                meta = MungGlyphMetadata.of_glyph(glyph)
                cv2.imwrite(
                    str(glyphs_folder / (
                        meta.mung_style + "_" + meta.mung_document
                        + "_" + str(meta.mung_node_id) + ".png"
                    )),
                    glyph_renderer.render(glyph)
                )
