from smashcima.assets.glyphs.mung.extraction.BaseSymbolExtractor \
    import BaseSymbolExtractor
from smashcima.assets.glyphs.mung.extraction.MungDocument \
    import MungDocument
from smashcima.assets.glyphs.mung.extraction.ExtractedBag \
    import ExtractedBag
from smashcima.assets.glyphs.mung.extraction.accidentals \
    import (get_accidental_center_from_notehead,
            get_accidental_center_from_central_hole)
from smashcima import px_to_mm, SmuflLabels, SmashcimaLabels, Glyph
from smashcima.geometry.Point import Point
from mung.node import Node
from .OmniOmrIjdarGlyphMetadata import OmniOmrIjdarGlyphMetadata


class OmniOmrIjdarSymbolExtractor(BaseSymbolExtractor):
    """Defines methods for extracting symbols from one MuNG document.
    Still needs to be overriden to define the metadata stamping logic."""

    def __init__(self, document: MungDocument, bag: ExtractedBag):
        super().__init__(document=document, bag=bag)

        self.TALL_BARLINE_THRESHOLD_MM = 16.0
        """When do we start considering barlines to be 'tall' (i.e. multi-staff).
        The average size of a staff (the 5 lines) is cca 8 millimeters."""

        self.BEAM_HOOK_MAX_WIDTH_MM = 2.0
        """Threshold that separates beams from beam hooks"""

        # metadata
        # (musicorpus page folder is named {book_uuid}_{page_uuid}
        # and contains the 'transcription.mung' file)
        document_uuid: str = self.document.path.parent.name
        parts = document_uuid.split("_")
        assert len(parts) == 2
        self.book_uuid: str = parts[0]
        self.page_uuid: str = parts[1]

        self.skipped_node_ids: set[int] = set()
        """MuNG nodes whose origin could not be determined
        (e.g. not linked to a staff), they are skipped entirely"""

    def emit_origin_point_on_staffline(self, node: Node, staffline_index_from_top: int):
        try:
            super().emit_origin_point_on_staffline(node, staffline_index_from_top)
        except AssertionError:
            self.skipped_node_ids.add(node.id)

    def emit_glyph_from_mung_node(self, node: Node, glyph_label: str):
        if node.id in self.skipped_node_ids:
            return
        super().emit_glyph_from_mung_node(node, glyph_label)

    def stamp_glyph(self, glyph: Glyph, node: Node):
        OmniOmrIjdarGlyphMetadata.stamp_glyph(
            glyph=glyph,
            node=node,
            book_uuid=self.book_uuid,
            page_uuid=self.page_uuid
        )

    ############################
    # Point Extraction Methods #
    ############################

    def extract_points_noteheadBlack(self):
        for node in self.iterate_nodes(["noteheadFull", "noteheadBlack"]):
            self.emit_origin_point(node, Point(0.5, 0.5))
    
    def extract_points_noteheadHalf(self):
        for node in self.iterate_nodes(["noteheadHalf", "noteheadWhole"]):
            self.emit_origin_point(node, Point(0.5, 0.5))
    
    def extract_points_restWhole(self):
        for node in self.iterate_nodes(["restWhole"]):
            self.emit_origin_point_on_staffline(node, 1) # second highest line
    
    def extract_points_restHalf(self):
        for node in self.iterate_nodes(["restHalf"]):
            self.emit_origin_point_on_staffline(node, 2) # middle line

    def extract_points_restQuarter(self):
        for node in self.iterate_nodes(["restQuarter"]):
            self.emit_origin_point_on_staffline(node, 2) # middle line
    
    def extract_points_rest8th(self):
        for node in self.iterate_nodes(["rest8th"]):
            self.emit_origin_point_on_staffline(node, 2) # middle line
    
    def extract_points_rest16th(self):
        for node in self.iterate_nodes(["rest16th"]):
            self.emit_origin_point_on_staffline(node, 2) # middle line

    def extract_points_barlineSingle(self):
        # TODO: barlines should be line glyphs with vertical position to
        # the edge stafflines recorded in a distribution (I guess)
        for node in self.iterate_nodes(["barline", "barlineSingle"],
            lambda n: px_to_mm(n.height, dpi=self.document.dpi) \
                < self.TALL_BARLINE_THRESHOLD_MM
        ):
            self.emit_origin_point(node, Point(0.5, 0.5))

    def extract_points_gClef(self):
        # TODO: non-standard clefs need to know which staffline to pick!
        for node in self.iterate_nodes(["gClef", "gClefChange"]):
            self.emit_origin_point_on_staffline(node, 3) # second lowest line
    
    def extract_points_fClef(self):
        # TODO: non-standard clefs need to know which staffline to pick!
        for node in self.iterate_nodes(["fClef"]):
            self.emit_origin_point_on_staffline(node, 1) # second highest line

    def extract_points_cClef(self):
        # TODO: non-standard clefs need to know which staffline to pick!
        # TODO: c-clef origin should also be picked by the staffline
        for node in self.iterate_nodes(["cClef", "cClefChange"]):
            self.emit_origin_point(node, Point(0.5, 0.5))
    
    def extract_points_stem(self):
        for node in self.iterate_nodes(["stem"]):
            self.emit_line_points(node, "↑")
    
    def extract_points_beam(self):
        # process together with beam hooks
        for node in self.iterate_nodes(["beam"]):
            self.emit_line_points(node, "→")
    
    def extract_points_beamHook(self):
        # already processed when extracting beams
        pass
    
    def extract_points_legerLine(self):
        for node in self.iterate_nodes(["legerLine"]):
            self.emit_line_points(node, "→")
    
    # ... flags

    def extract_points_augmentationDot(self):
        for node in self.iterate_nodes(["augmentationDot"]):
            self.emit_origin_point(node, Point(0.5, 0.5))
    
    def extract_points_articStaccatoBelow(self):
        for node in self.iterate_nodes(["articStaccatoBelow", "articStaccatoAbove"]):
            self.emit_origin_point(node, Point(0.5, 0.5))
    
    def extract_points_accidentalSharp(self):
        for node in self.iterate_nodes(["accidentalSharp"]):
            origin = get_accidental_center_from_central_hole(node) \
                or get_accidental_center_from_notehead(node, self.graph) \
                or Point(0.5, 0.5) # center
            self.emit_origin_point(node, origin)

    def extract_points_accidentalFlat(self):
        for node in self.iterate_nodes(["accidentalFlat"]):
            origin = get_accidental_center_from_central_hole(node) \
                or get_accidental_center_from_notehead(node, self.graph) \
                or Point(0.5, 0.75) # slightly lower than center
            self.emit_origin_point(node, origin)

    def extract_points_accidentalNatural(self):
        for node in self.iterate_nodes(["accidentalNatural"]):
            origin = get_accidental_center_from_central_hole(node) \
                or get_accidental_center_from_notehead(node, self.graph) \
                or Point(0.5, 0.5) # center
            self.emit_origin_point(node, origin)

    def extract_points_accidentalDoubleSharp(self):
        for node in self.iterate_nodes(["accidentalDoubleSharp"]):
            origin = get_accidental_center_from_notehead(node, self.graph) \
                or Point(0.5, 0.5) # center
            self.emit_origin_point(node, origin)
    
    def extract_points_accidentalDoubleFlat(self):
        for node in self.iterate_nodes(["accidentalDoubleFlat"]):
            origin = get_accidental_center_from_central_hole(node) \
                or get_accidental_center_from_notehead(node, self.graph) \
                or Point(0.5, 0.75) # slightly lower than center
            self.emit_origin_point(node, origin)
    
    def extract_points_bracket(self):
        for node in self.iterate_nodes(["bracket"]):
            self.emit_line_points(node, "↓")
        
    def extract_points_brace(self):
        for node in self.iterate_nodes(["brace"]):
            self.emit_line_points(node, "↓")
    
    def extract_points_timeSig(self):
        for node in self.iterate_nodes(set([
            "numeral0", "numeral1", "numeral2", "numeral3", "numeral4",
            "numeral5", "numeral6", "numeral7", "numeral8", "numeral9",
            # TODO: what about numeral "12" which is present in OmniOMR?
            "timeSig0", "timeSig1", "timeSig2", "timeSig3", "timeSig4",
            "timeSig5", "timeSig6", "timeSig7", "timeSig8", "timeSig9",
            "timeSigCommon", "timeSigCutCommon"
        ])):
            if self.graph.has_parents(node, ["timeSignature"]):
                self.emit_origin_point(node, Point(0.5, 0.5))

    ############################
    # Delta Extraction Methods #
    ############################

    # ...
    
    ############################
    # Glyph Extraction Methods #
    ############################
    
    def extract_glyphs_noteheadBlack(self):
        for node in self.iterate_nodes(["noteheadFull", "noteheadBlack"],
            lambda n: not self.graph.has_children(n, ["legerLine"])
        ):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.noteheadBlack.value
            )
    
    def extract_glyphs_noteheadWhole(self):
        for node in self.iterate_nodes(["noteheadHalf", "noteheadWhole"],
            lambda n: not self.graph.has_children(n, ["legerLine"])
        ):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.noteheadWhole.value
            )

    def extract_glyphs_restWhole(self):
        for node in self.iterate_nodes(["restWhole"]):
            self.emit_glyph_from_mung_node(node, SmuflLabels.restWhole.value)
    
    def extract_glyphs_restHalf(self):
        for node in self.iterate_nodes(["restHalf"]):
            self.emit_glyph_from_mung_node(node, SmuflLabels.restHalf.value)

    def extract_glyphs_restQuarter(self):
        for node in self.iterate_nodes(["restQuarter"]):
            self.emit_glyph_from_mung_node(node, SmuflLabels.restQuarter.value)
    
    def extract_glyphs_rest8th(self):
        for node in self.iterate_nodes(["rest8th"]):
            self.emit_glyph_from_mung_node(node, SmuflLabels.rest8th.value)
    
    def extract_glyphs_rest16th(self):
        for node in self.iterate_nodes(["rest16th"]):
            self.emit_glyph_from_mung_node(node, SmuflLabels.rest16th.value)

    def extract_glyphs_barlineSingle(self):
        # TODO: barlines should be line glyphs with vertical position to
        # the edge stafflines recorded in a distribution (I guess)
        for node in self.iterate_nodes(["barline", "barlineSingle"],
            lambda n: px_to_mm(n.height, dpi=self.document.dpi) \
                < self.TALL_BARLINE_THRESHOLD_MM
        ):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.barlineSingle.value
            )

    def extract_glyphs_gClef(self):
        for node in self.iterate_nodes(["gClef", "gClefChange"]):
            self.emit_glyph_from_mung_node(node, SmuflLabels.gClef.value)
    
    def extract_glyphs_fClef(self):
        for node in self.iterate_nodes(["fClef"]):
            self.emit_glyph_from_mung_node(node, SmuflLabels.fClef.value)

    def extract_glyphs_cClef(self):
        for node in self.iterate_nodes(["cClef", "cClefChange"]):
            self.emit_glyph_from_mung_node(node, SmuflLabels.cClef.value)
    
    def extract_glyphs_stem(self):
        for node in self.iterate_nodes(["stem"]):
            self.emit_line_glyph_from_mung_node(node, SmuflLabels.stem.value)
    
    def extract_glyphs_beam(self):
        # TODO: separate beam hooks by notation graph, not size
        for node in self.iterate_nodes(["beam"],
            lambda n: px_to_mm(n.width, dpi=self.document.dpi) \
                > self.BEAM_HOOK_MAX_WIDTH_MM
        ):
            self.emit_line_glyph_from_mung_node(
                node, SmashcimaLabels.beam.value
            )
    
    def extract_glyphs_beamHook(self):
        # TODO: separate beam hooks by notation graph, not size
        for node in self.iterate_nodes(["beam"],
            lambda n: px_to_mm(n.width, dpi=self.document.dpi) \
                <= self.BEAM_HOOK_MAX_WIDTH_MM
        ):
            self.emit_line_glyph_from_mung_node(
                node, SmashcimaLabels.beamHook.value
            )
    
    def extract_glyphs_legerLine(self):
        for node in self.iterate_nodes(["legerLine"]):
            self.emit_line_glyph_from_mung_node(
                node, SmashcimaLabels.legerLine.value
            )
    
    # ... flags

    def extract_glyphs_augmentationDot(self):
        for node in self.iterate_nodes(["augmentationDot"]):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.augmentationDot.value
            )
    
    def extract_glyphs_articStaccatoBelow(self):
        for node in self.iterate_nodes(["articStaccatoBelow", "articStaccatoAbove"]):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.articStaccatoBelow.value
            )
    
    def extract_glyphs_accidentalSharp(self):
        for node in self.iterate_nodes(["accidentalSharp"]):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.accidentalSharp.value
            )

    def extract_glyphs_accidentalFlat(self):
        for node in self.iterate_nodes(["accidentalFlat"]):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.accidentalFlat.value
            )

    def extract_glyphs_accidentalNatural(self):
        for node in self.iterate_nodes(["accidentalNatural"]):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.accidentalNatural.value
            )

    def extract_glyphs_accidentalDoubleSharp(self):
        for node in self.iterate_nodes(["accidentalDoubleSharp"]):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.accidentalDoubleSharp.value
            )
    
    def extract_glyphs_accidentalDoubleFlat(self):
        for node in self.iterate_nodes(["accidentalDoubleFlat"]):
            self.emit_glyph_from_mung_node(
                node, SmuflLabels.accidentalDoubleFlat.value
            )

    def extract_glyphs_bracket(self):
        for node in self.iterate_nodes(["bracket"]):
            self.emit_line_glyph_from_mung_node(
                node, SmuflLabels.bracket.value
            )

    def extract_glyphs_brace(self):
        for node in self.iterate_nodes(["brace"]):
            self.emit_line_glyph_from_mung_node(
                node, SmuflLabels.brace.value
            )

    def extract_glyphs_timeSig(self) -> None:
        _GLYPH_CLASS_LOOKUP: dict[str, str] = {
            "numeral0": SmuflLabels.timeSig0.value,
            "numeral1": SmuflLabels.timeSig1.value,
            "numeral2": SmuflLabels.timeSig2.value,
            "numeral3": SmuflLabels.timeSig3.value,
            "numeral4": SmuflLabels.timeSig4.value,
            "numeral5": SmuflLabels.timeSig5.value,
            "numeral6": SmuflLabels.timeSig6.value,
            "numeral7": SmuflLabels.timeSig7.value,
            "numeral8": SmuflLabels.timeSig8.value,
            "numeral9": SmuflLabels.timeSig9.value,
            # TODO: what about numeral "12" which is present in OmniOMR?
            **{
                f"timeSig{d}": getattr(SmuflLabels, f"timeSig{d}").value
                for d in range(10)
            },
            "timeSigCommon": SmuflLabels.timeSigCommon.value,
            "timeSigCutCommon": SmuflLabels.timeSigCutCommon.value,
        }

        for time_signature in self.iterate_nodes(["timeSignature"]):
            for time_mark in self.graph.children(
                time_signature,
                list(_GLYPH_CLASS_LOOKUP.keys())
            ):
                self.emit_glyph_from_mung_node(
                    node=time_mark,
                    glyph_label=_GLYPH_CLASS_LOOKUP[time_mark.class_name],
                )
