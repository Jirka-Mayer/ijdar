import copy
import xml.etree.ElementTree as ET
from pathlib import Path

from lmx.musicxml.io.read_musicxml_tree_from_file import read_musicxml_tree_from_file
from lmx.musicxml.io.write_musicxml_tree_to_file import write_musicxml_tree_to_file

# order of children of the <attributes> element, as defined by MusicXML
_ATTRIBUTES_ORDER = [
    "footnote", "level", "divisions", "key", "time", "staves",
    "part-symbol", "instruments", "clef", "staff-details",
    "transpose", "for-part", "directive", "measure-style",
]


def prepare_smashcima_input_file(input_musicxml_path: Path, output_musicxml_path: Path):
    """
    Works around Smashcima MusicXML loader limitations, without changing
    what is rendered. The result is only used as the Smashcima input,
    the dataset MusicXML and LMX stay unchanged.

    - Smashcima keeps only the last <attributes> element at a given onset,
      so consecutive <attributes> elements are merged into one.
    - Smashcima requires a key signature in the first attributes,
      so a null key signature (which is never rendered) is added if missing.
    - Smashcima has no glyphs for breve and longer notes and rests,
      so these are rendered as whole notes and rests.
    - Smashcima supports only alter values -1, 0, +1, so double sharps
      and flats are clamped (the drawn accidental is given by <accidental>).
    - Accidentals that have no glyphs (anything other than sharp,
      flat and natural) are removed (not drawn).
    """
    musicxml_tree = read_musicxml_tree_from_file(input_musicxml_path)
    for part_element in musicxml_tree.findall("part"):
        for measure_element in part_element.findall("measure"):
            _merge_consecutive_attributes(measure_element)
        _ensure_header_key(part_element)
        _replace_long_durations(part_element)
        _fix_alters_and_accidentals(part_element)
    write_musicxml_tree_to_file(output_musicxml_path, musicxml_tree)


def _merge_consecutive_attributes(measure_element: ET.Element):
    """Merges <attributes> elements not separated by a time-moving element"""
    current: ET.Element | None = None
    for child in list(measure_element):
        if child.tag in ("note", "backup", "forward"):
            current = None
        elif child.tag == "attributes":
            if current is None:
                current = child
            else:
                for grandchild in list(child):
                    _replace_or_append(current, grandchild)
                measure_element.remove(child)


def _replace_or_append(attributes_element: ET.Element, new_child: ET.Element):
    """Inserts a child into <attributes>, replacing the same-tag child
    with the same staff number, and keeps the MusicXML element order"""
    for old_child in attributes_element.findall(new_child.tag):
        if old_child.attrib.get("number") == new_child.attrib.get("number"):
            attributes_element.remove(old_child)
    _insert_in_order(attributes_element, new_child)


def _insert_in_order(attributes_element: ET.Element, new_child: ET.Element):
    order = _ATTRIBUTES_ORDER.index(new_child.tag) \
        if new_child.tag in _ATTRIBUTES_ORDER else len(_ATTRIBUTES_ORDER)
    index = 0
    for i, child in enumerate(attributes_element):
        child_order = _ATTRIBUTES_ORDER.index(child.tag) \
            if child.tag in _ATTRIBUTES_ORDER else len(_ATTRIBUTES_ORDER)
        if child_order <= order:
            index = i + 1
    attributes_element.insert(index, copy.deepcopy(new_child))


def _ensure_header_key(part_element: ET.Element):
    measure_element = part_element.find("measure")
    if measure_element is None:
        return
    attributes_element = measure_element.find("attributes")
    if attributes_element is None:
        return
    if attributes_element.find("key") is None:
        _insert_in_order(
            attributes_element,
            ET.fromstring("<key><fifths>0</fifths></key>")
        )


def _replace_long_durations(part_element: ET.Element):
    for type_element in part_element.iterfind("measure/note/type"):
        if type_element.text in ("breve", "long", "maxima"):
            type_element.text = "whole"


def _fix_alters_and_accidentals(part_element: ET.Element):
    supported_accidentals = {"sharp", "flat", "natural"}
    for note_element in part_element.iterfind("measure/note"):
        alter_element = note_element.find("pitch/alter")
        if alter_element is not None and alter_element.text is not None:
            alter = round(float(alter_element.text))
            alter_element.text = str(max(-1, min(1, alter)))
        accidental_element = note_element.find("accidental")
        if accidental_element is not None \
                and accidental_element.text not in supported_accidentals:
            note_element.remove(accidental_element)
