import random
from pathlib import Path

import cv2
import numpy as np
import smashcima as sc
from smashcima.scene.AffineSpace import AffineSpace
from smashcima.scene.visual.StaffVisual import StaffVisual
from smashcima.synthesis.PageSynthesizer import PageSynthesizer


class NotationOverflowError(Exception):
    """Raised when the synthesized notation does not fit into the image,
    which would make the image not match its LMX annotation"""
    pass


class SoloStaffPageSynthesizer(sc.synthesis.SimplePageSynthesizer):
    """Page synthesizer that places exactly one staff onto the page,
    vertically centered (the simple synthesizer divides by zero
    when asked for one staff)"""

    def _synthesize_stafflines(self, page_space: AffineSpace) -> list[StaffVisual]:
        ps = self.page_setup
        assert ps.staff_count == 1
        content_width = ps.size.x - (ps.padding_left + ps.padding_right)
        content_height = ps.size.y - (ps.padding_top + ps.padding_bottom)
        staff = self.stafflines_synthesizer.synthesize_stafflines(
            page_space=page_space,
            position=sc.Vector2(
                ps.padding_left,
                ps.padding_top + content_height / 2
            ),
            width=content_width
        )
        return [staff]


class SoloStaffModel(sc.orchestration.BaseHandwrittenModel):
    """Model that synthesizes solo staves with MUSCIMA++ glyphs"""

    PADDING = 2.0
    """Page padding around the staff, in staff heights. Must be large enough
    to fit ledger lines and stems, the rest is cropped away afterwards."""

    VERTICAL_MARGIN = 1.0
    """How much space to leave above and below the staff in the final
    image after cropping, in staff heights"""

    HORIZONTAL_MARGIN = 1.0
    """How much space to leave left and right of the staff in the final
    image after cropping, in staff heights"""

    MAX_PAGE_WIDTH_PX = 30_000
    """Pages wider than this (at the default 300 DPI) are rasterized
    with a lower DPI"""

    def __init__(self, width_magic_factor: float):
        super().__init__()
        self.width_magic_factor = width_magic_factor

    def register_services(self):
        super().register_services()

        # replace the page synthesizer with the solo-staff one
        self.container.type(SoloStaffPageSynthesizer)
        self.container.interface(PageSynthesizer, SoloStaffPageSynthesizer)

    def resolve_services(self) -> None:
        super().resolve_services()

        # page synthesizer is actually the SoloStaffPageSynthesizer
        self.page_synthesizer: SoloStaffPageSynthesizer \
            = self.page_synthesizer

        # layout synthesizer is actually ColumnMusicNotationSynthesizer
        self.notation_synthesizer: sc.synthesis.ColumnMusicNotationSynthesizer \
            = self.notation_synthesizer

    def configure_services(self):
        super().configure_services()

        # disable system breaks all together
        self.notation_synthesizer.disable_wrapping = True
        self.notation_synthesizer.respect_line_and_page_breaks = False

    def __call__(
            self,
            file: Path | str,
            notation_width: float,
            sample_seed: int,
            output_height: int | None,
            no_augmentation: bool,
    ) -> np.ndarray:
        """
        :param file: Path to the .musicxml file to synthesize
        :param notation_width: Width of the notation when engraved
            by MuseScore, in staff heights. The staff width is this number
            multiplied by the width magic factor.
        :param sample_seed: Seed for all the randomness of this sample.
        :param output_height: Height of the output image in pixels,
            None keeps the full resolution.
        :param no_augmentation: Disables postprocessing image augmentations.
        """
        # set rng seed for this synthetic sample
        # (and for cv2 and numpy as well since postprocessing filters
        # don't respect the random.Random instance in smashcima)
        self.rng.seed(sample_seed)

        # also set seed on global generators to make sure there is
        # absolutely no uncontrolled randomness
        random.seed(sample_seed)
        np.random.seed(sample_seed % (2 ** 31))
        cv2.setRNGSeed(sample_seed % (2 ** 31))

        # configure page size and layout
        staff_height = self.page_synthesizer.stafflines_synthesizer.staff_height

        staff_width = notation_width * staff_height * self.width_magic_factor

        ps = self.page_synthesizer.page_setup
        ps.padding_top = staff_height * self.PADDING
        ps.padding_bottom = staff_height * self.PADDING
        ps.padding_left = staff_height * self.PADDING
        ps.padding_right = staff_height * self.PADDING
        ps.staff_count = 1
        ps.size = sc.Vector2(
            staff_width + 2 * staff_height * self.PADDING,
            staff_height * (1 + 2 * self.PADDING)
        )

        # stretch out notation to full width in 50% of cases
        self.notation_synthesizer.stretch_out_columns = self.rng.random() < 0.5

        # run synthesis
        scene = super().__call__(file=file)
        assert len(scene.pages) == 1
        self._check_notation_overflow(scene)

        # configure postprocessing (image augmentations)
        if not no_augmentation:
            pp = sc.BaseHandwrittenPostprocessor(self.rng)
            pp.f_scribbles.force_dont = True # handling fonts is a mess
            scene.compositor = sc.DefaultCompositor(pp)

        # lower the DPI for extremely long staves, since OpenCV (used by
        # the postprocessing filters) does not support images wider
        # than 32767 pixels
        scene.dpi = min(scene.dpi, self.MAX_PAGE_WIDTH_PX / sc.mm_to_px(ps.size.x, dpi=1))

        # rasterize scene
        bitmap = scene.render(scene.pages[0])

        # crop away the excess padding
        crop_v = int(sc.mm_to_px(
            staff_height * (self.PADDING - self.VERTICAL_MARGIN), dpi=scene.dpi
        ))
        crop_h = int(sc.mm_to_px(
            staff_height * (self.PADDING - self.HORIZONTAL_MARGIN), dpi=scene.dpi
        ))
        bitmap = bitmap[crop_v:-crop_v, crop_h:-crop_h, :]

        # scale down the image to reduce dataset size on disk and in RAM
        if output_height is not None:
            scale_ratio = (output_height / bitmap.shape[0])
            bitmap = cv2.resize(
                bitmap,
                dsize=(
                    int(bitmap.shape[1] * scale_ratio),
                    output_height
                ),
                interpolation=cv2.INTER_AREA
            )

        return bitmap

    def _check_notation_overflow(self, scene: sc.Scene):
        """Raises an exception if some glyphs stick out past the end of the
        staff further than the horizontal margin (they would be cropped away).
        This happens when the musical content is too dense for the image
        width given by the aspect ratio hint."""
        page = scene.pages[0]
        assert len(page.staves) == 1
        staff = page.staves[0]
        staff_bbox = staff.glyph.get_bbox_in_space(page.space)
        limit = staff_bbox.right + staff.staff_height * self.HORIZONTAL_MARGIN

        rightmost = max(
            glyph.get_bbox_in_space(page.space).right
            for glyph in scene.find(sc.Glyph)
        )
        if rightmost > limit:
            raise NotationOverflowError(
                f"Notation overflows the staff end by "
                f"{(rightmost - staff_bbox.right) / staff.staff_height:.1f} "
                f"staff heights"
            )
