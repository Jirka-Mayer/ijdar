import random
from smashcima import SmuflLabels
from smashcima.scene.Glyph import Glyph
from smashcima.synthesis.glyph.MuscimaPPGlyphSynthesizer \
    import LABEL_MAP as MPP_LABEL_MAP, MuscimaPPGlyphSynthesizer
from smashcima.synthesis.glyph.RepositoryGlyphSynthesizer \
    import RepositoryGlyphSynthesizer
from .OmniOmrIjdarStyleDomain import OmniOmrIjdarStyleDomain
from .OmniOmrIjdarGlyphs import OmniOmrIjdarGlyphs


LABEL_MAP = {
    **MPP_LABEL_MAP
}

# flags are currently not supported by this synth,
# they will use the fallback synth
del LABEL_MAP[SmuflLabels.flag8thUp.value]
del LABEL_MAP[SmuflLabels.flag8thDown.value]
del LABEL_MAP[SmuflLabels.flag16thUp.value]
del LABEL_MAP[SmuflLabels.flag16thDown.value]
FLAGS = [
    SmuflLabels.flag8thUp.value,
    SmuflLabels.flag8thDown.value,
    SmuflLabels.flag16thUp.value,
    SmuflLabels.flag16thDown.value,
]


class OmniOmrIjdarGlyphSynthesizer(RepositoryGlyphSynthesizer):
    """Synthesizes glyphs by sampling from the OmniOMR dataset"""
    
    def __init__(
        self,
        omniomr_glyphs: OmniOmrIjdarGlyphs,
        style_domain: OmniOmrIjdarStyleDomain,
        fallback_synthesizer: MuscimaPPGlyphSynthesizer,
        rng: random.Random
    ):
        symbol_repository = omniomr_glyphs.load_symbol_repository()

        super().__init__(
            symbol_repository=symbol_repository,
            style_domain=style_domain,
            rng=rng
        )

        self.fallback_synthesizer = fallback_synthesizer

    def supports_label(self, label: str) -> bool:
        return (label in LABEL_MAP) or (label in FLAGS)
    
    def create_glyph(self, label: str) -> Glyph:
        # with flags, fall back on MPP
        if label in FLAGS:
            return self.fallback_synthesizer.create_glyph(label)
        
        glyph = super().create_glyph(LABEL_MAP[label])

        # adjust glyph label to match what the user wants
        # (because the label map is not 1:1)
        glyph.label = label

        return glyph
