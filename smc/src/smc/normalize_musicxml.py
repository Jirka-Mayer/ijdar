import copy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from lmx.musicxml.io.read_musicxml_tree_from_file import read_musicxml_tree_from_file
from lmx.musicxml.io.write_musicxml_tree_to_file import write_musicxml_tree_to_file
from lmx.musicxml.omitted_staff_header.normalize_invisible_key_signature import (
    normalize_invisible_key_signature,
)
from lmx.musicxml.omitted_staff_header.normalize_invisible_time_signature import (
    normalize_invisible_time_signature,
)
from lmx.musicxml.omitted_staff_header.set_header_key_visibility import (
    set_header_key_visibility,
)
from lmx.musicxml.omitted_staff_header.set_header_time_visibility import (
    set_header_time_visibility,
)
from lmx.tokenization.Encoder import Encoder


def normalize_musicxml_file(
        input_musicxml_path: Path,
        output_musicxml_path: Path,
        output_lmx_path: Path,
):
    """
    Loads a solo-staff MusicXML file, removes all key signatures and
    time signatures from it (because Smashcima cannot render them),
    writes the modified MusicXML and also its LMX encoding.

    Other things that Smashcima does not render (slurs, tuplets,
    articulations, ...) are deliberately kept in the MusicXML and LMX.
    """
    musicxml_tree = read_musicxml_tree_from_file(input_musicxml_path)
    part_elements = musicxml_tree.findall("part")
    assert len(part_elements) == 1, "Expected exactly one <part> element"

    musicxml_tree.getroot().remove(part_elements[0])
    part_element = remove_key_and_time_signatures(part_elements[0])
    musicxml_tree.getroot().append(part_element)

    lmx_encoder = Encoder(errout=sys.stderr)
    lmx_encoder.process_part(part_element)
    lmx_string = " ".join(lmx_encoder.output_tokens)

    write_musicxml_tree_to_file(output_musicxml_path, musicxml_tree)
    output_lmx_path.write_text(lmx_string, "utf-8")


def remove_key_and_time_signatures(part_element: ET.Element) -> ET.Element:
    """
    Returns a copy of the given <part> element with all key signatures
    and time signatures removed, while preserving the visual appearance
    of notes (i.e. the alter values are recomputed from visible accidentals).

    Key and time changes inside the part are deleted. The header key
    signature (if present) is set to the null key signature (fifths:0),
    which is consistent with how null keys appear in the rest of the zeus
    datasets. The header time signature is removed, which is consistent
    with how zeus normalizes invisible time signatures.
    """
    part_element = copy.deepcopy(part_element)

    # remove all non-header key and time signatures (changes)
    for measure_index, measure_element in enumerate(part_element.findall("measure")):
        for attributes_element in measure_element.findall("attributes"):
            is_header = measure_index == 0 and _is_at_onset_zero(
                measure_element, attributes_element
            )
            if is_header:
                continue
            for element in attributes_element.findall("key") \
                    + attributes_element.findall("time"):
                attributes_element.remove(element)
            if len(attributes_element) == 0:
                measure_element.remove(attributes_element)

    # make header signatures invisible, so that they get normalized
    if part_element.find("measure") is not None:
        try:
            set_header_key_visibility(part_element, "invisible")
            set_header_time_visibility(part_element, "invisible")
        except ValueError:
            pass  # no header attributes, so no header signatures

    # normalize the header key to the null key
    # (this also runs the repair_alters function, which recomputes
    # alter values for the notes affected by the removed key changes)
    part_element = normalize_invisible_key_signature(
        part_element=part_element,
        desired_key=0,
        when_key_visible="raise-exception",
    )

    # remove the header time signature
    part_element = normalize_invisible_time_signature(
        part_element=part_element,
        desired_time=None,
        when_time_visible="raise-exception",
    )

    return part_element


def _is_at_onset_zero(
        measure_element: ET.Element,
        attributes_element: ET.Element
) -> bool:
    """Returns true if no time-advancing element precedes the attributes"""
    for child in measure_element:
        if child is attributes_element:
            return True
        if child.tag in ("note", "forward"):
            if child.find("chord") is None and child.find("grace") is None:
                return False
    return True
