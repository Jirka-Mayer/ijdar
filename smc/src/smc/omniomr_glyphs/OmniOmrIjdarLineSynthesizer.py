import random
from smashcima.geometry.Vector2 import Vector2
from smashcima.scene.LineGlyph import LineGlyph
from smashcima.synthesis.glyph.MuscimaPPLineSynthesizer \
    import LABEL_MAP as MPP_LABEL_MAP
from smashcima.synthesis.glyph.RepositoryLineSynthesizer \
    import RepositoryLineSynthesizer
from .OmniOmrIjdarStyleDomain import OmniOmrIjdarStyleDomain
from .OmniOmrIjdarGlyphs import OmniOmrIjdarGlyphs


LABEL_MAP = {
    **MPP_LABEL_MAP
}


class OmniOmrIjdarLineSynthesizer(RepositoryLineSynthesizer):
    """Synthesizes line glyphs by sampling from the OmniOMR dataset"""
    
    def __init__(
        self,
        omniomr_glyphs: OmniOmrIjdarGlyphs,
        style_domain: OmniOmrIjdarStyleDomain,
        rng: random.Random
    ):
        symbol_repository = omniomr_glyphs.load_symbol_repository()

        super().__init__(
            symbol_repository=symbol_repository,
            style_domain=style_domain,
            rng=rng
        )

    def supports_label(self, label: str) -> bool:
        return label in LABEL_MAP
    
    def create_glyph(self, label: str, delta: Vector2) -> LineGlyph:
        glyph = super().create_glyph(LABEL_MAP[label], delta)

        # adjust glyph label to match what the user wants
        # (because the label map is not 1:1)
        glyph.label = label

        return glyph
