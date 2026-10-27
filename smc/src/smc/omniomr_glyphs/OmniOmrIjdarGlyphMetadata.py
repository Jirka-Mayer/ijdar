from dataclasses import dataclass
from typing import Optional
from mung.node import Node
from smashcima.scene import Glyph
from smashcima.assets.glyphs.mung.MungGlyphMetadata import MungGlyphMetadata


@dataclass
class OmniOmrIjdarGlyphMetadata(MungGlyphMetadata):
    """Metadata information object for a glyph from the OmniOMR dataset"""
    
    @property
    def book_uuid(self) -> str:
        """UUID of the book from the Moravská zemská knihovna (MZK)"""
        return self.mung_style

    page_uuid: str
    """UUID of the page from the Moravská zemská knihovna (MZK)"""

    @staticmethod
    def stamp_glyph(
        glyph: Glyph,
        node: Node,
        book_uuid: str,
        page_uuid: str
    ):
        # just create an instance and that's it
        # the glyph's inlinks will hold on to the instance
        OmniOmrIjdarGlyphMetadata(
            glyph=glyph,
            mung_style=book_uuid,
            mung_document=node.document,
            mung_node_id=node.id,
            page_uuid=page_uuid
        )
    
    @classmethod
    def of_glyph(cls, glyph: Glyph):
        return cls.of(glyph, lambda m: m.glyph)

    @classmethod
    def of_glyph_or_none(cls, glyph: Optional[Glyph]):
        return cls.of_or_none(glyph, lambda m: m.glyph)

