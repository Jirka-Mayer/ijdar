import smashcima as sc
from smashcima.assets.AssetRepository import AssetRepository

from .omniomr_glyphs.OmniOmrIjdarGlyphs import OmniOmrIjdarGlyphs
from .omniomr_glyphs.OmniOmrIjdarGlyphSynthesizer import OmniOmrIjdarGlyphSynthesizer
from .omniomr_glyphs.OmniOmrIjdarLineSynthesizer import OmniOmrIjdarLineSynthesizer
from .omniomr_glyphs.OmniOmrIjdarStyleDomain import OmniOmrIjdarStyleDomain
from .SoloStaffModel import SoloStaffModel


class OmniOmrSoloStaffModel(SoloStaffModel):
    """Model that synthesizes solo staves with OmniOMR glyphs"""

    def register_services(self):
        super().register_services()

        # install and resolve the glyphs asset bundle
        self.container.instance(
            OmniOmrIjdarGlyphs,
            self.container.resolve(AssetRepository).resolve_bundle(
                OmniOmrIjdarGlyphs
            )
        )

        # register the style domain
        self.container.type(OmniOmrIjdarStyleDomain)

        # register glyph synth
        self.container.type(OmniOmrIjdarGlyphSynthesizer)
        self.container.interface(
            sc.GlyphSynthesizer,
            OmniOmrIjdarGlyphSynthesizer
        )

        # register line synth
        self.container.type(OmniOmrIjdarLineSynthesizer)
        self.container.interface(
            sc.LineSynthesizer,
            OmniOmrIjdarLineSynthesizer
        )
