import random

from .OmniOmrIjdarGlyphs import OmniOmrIjdarGlyphs

from smashcima.synthesis.style.RepositoryStyleDomain import RepositoryStyleDomain


class OmniOmrIjdarStyleDomain(RepositoryStyleDomain):
    def __init__(self, omniomr_glyphs: OmniOmrIjdarGlyphs, rng: random.Random):
        symbol_repository = omniomr_glyphs.load_symbol_repository()

        super().__init__(
            symbol_repository=symbol_repository,
            rng=rng
        )
