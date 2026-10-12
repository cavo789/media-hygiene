"""Put our words into a sidecar without taking anything of anybody else's.

- `dc:subject` gets the words this tool produces, after those already there; the
  words it wrote last time (`mh:subjects`) and no longer produces are taken back, and
  a word it wrote that is gone (removed in another application) is not added again.
- `dc:description` gets the model's sentence only when empty, or when it still holds
  the sentence this tool wrote last time (`mh:description`).
- The town, the country and the user's place go into the location fields: `xmp_places`.
- A new sidecar says who wrote it (`xmp:CreatorTool`): see `xmp_owner`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.tags import xmp_places
from media_hygiene.tags.xmp_doc import (
    ABOUT,
    ALT,
    BAG,
    DC_NS,
    DEFAULT_LANG,
    LANG,
    LI,
    MH_NS,
    RDF_NS,
    X_NS,
    XMP_NS,
    XmpDoc,
    items,
    text_of,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

SUBJECT: Final = f"{{{DC_NS}}}subject"
CAPTION: Final = f"{{{DC_NS}}}description"
CREATOR: Final = f"{{{XMP_NS}}}CreatorTool"
_MH_SUBJECTS: Final = f"{{{MH_NS}}}subjects"
_MH_CAPTION: Final = f"{{{MH_NS}}}description"
_XPACKET_BEGIN: Final = '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
_XPACKET_END: Final = '\n<?xpacket end="w"?>\n'
_TOOLKIT: Final = f"{{{X_NS}}}xmptk"
_INDENT: Final = " "


@dataclass(frozen=True, slots=True)
class XmpValues:
    """What this tool writes for one file: its words, the sentence, the place."""

    subjects: tuple[str, ...]
    description: str = ""
    places: xmp_places.XmpPlaces = xmp_places.NO_PLACES


def merge(doc: XmpDoc, values: XmpValues) -> bool:
    """Merge our values into a sidecar, in place.

    Args:
        doc: The sidecar.
        values: Our words and sentence of today.

    Returns:
        True when a value changed: the sidecar is then to be written.
    """
    before = _snapshot(doc)
    _merge(doc, values)
    xmp_places.merge_places(doc, values.places)
    return _snapshot(doc) != before


def _snapshot(doc: XmpDoc) -> tuple[object, ...]:
    """The values `merge` may change.

    Args:
        doc: The sidecar.

    Returns:
        Its words, ours, its sentence, ours, its location fields and ours.
    """
    return (
        items(doc.find(SUBJECT)),
        items(doc.find(_MH_SUBJECTS)),
        _caption(doc),
        text_of(doc.find(_MH_CAPTION)),
        xmp_places.places_snapshot(doc),
    )


def _merge(doc: XmpDoc, values: XmpValues) -> None:
    """Merge our values into a sidecar, in place.

    Args:
        doc: The sidecar.
        values: Our words and sentence of today.
    """
    present = items(doc.find(SUBJECT))
    written = items(doc.find(_MH_SUBJECTS))
    wanted = values.subjects
    added = [word for word in wanted if word not in written and word not in present]
    stale = {word for word in present if word in written and word not in wanted}
    _set_list(doc, SUBJECT, [word for word in present if word not in stale] + added)
    _set_list(doc, _MH_SUBJECTS, [word for word in written if word in wanted] + added)
    current = _caption(doc)
    ours = text_of(doc.find(_MH_CAPTION))
    if current and current != ours:
        return  # somebody else's sentence: kept
    _set_caption(doc, values.description)


def new_document(values: XmpValues, tool: str) -> XmpDoc:
    """Make a new sidecar holding our values only.

    Args:
        values: Our words and sentence.
        tool: `media-hygiene <version>`.

    Returns:
        The document.
    """
    root = ET.Element(f"{{{X_NS}}}xmpmeta", {_TOOLKIT: tool})
    rdf = ET.SubElement(root, f"{{{RDF_NS}}}RDF")
    description = ET.SubElement(rdf, f"{{{RDF_NS}}}Description", {ABOUT: ""})
    ET.SubElement(description, CREATOR).text = tool
    doc = XmpDoc(_XPACKET_BEGIN, root, _XPACKET_END, ())
    merge(doc, values)
    ET.indent(root, space=_INDENT)
    return doc


def _caption(doc: XmpDoc) -> str:
    """The sentence of a sidecar: its default language, else its first.

    Args:
        doc: The sidecar.

    Returns:
        The sentence, or an empty string.
    """
    element = doc.find(CAPTION)
    if element is None:
        return ""
    for item in element.iter(LI):
        if item.get(LANG) == DEFAULT_LANG:
            return (item.text or "").strip()
    found = items(element)
    return found[0] if found else ""


def _set_caption(doc: XmpDoc, sentence: str) -> None:
    """Write (or take back) our sentence, and remember it.

    Args:
        doc: The sidecar.
        sentence: The sentence; empty takes ours back.
    """
    _remove(doc, CAPTION)
    _remove(doc, _MH_CAPTION)
    if not sentence:
        return
    home = doc.descriptions()[0]
    alt = ET.SubElement(ET.SubElement(home, CAPTION), ALT)
    ET.SubElement(alt, LI, {LANG: DEFAULT_LANG}).text = sentence
    ET.SubElement(home, _MH_CAPTION).text = sentence


def _set_list(doc: XmpDoc, tag: str, values: Sequence[str]) -> None:
    """Write a bag property where it is (in the first description when new).

    Args:
        doc: The sidecar.
        tag: The property.
        values: Its values; none removes it.
    """
    element = doc.find(tag)
    if not values:
        _remove(doc, tag)
        return
    if element is None:
        element = ET.SubElement(doc.descriptions()[0], tag)
    for child in list(element):
        element.remove(child)
    bag = ET.SubElement(element, BAG)
    for value in values:
        ET.SubElement(bag, LI).text = value


def _remove(doc: XmpDoc, tag: str) -> None:
    """Remove a property from every description.

    Args:
        doc: The sidecar.
        tag: The property.
    """
    for each in doc.descriptions():
        for child in each.findall(tag):
            each.remove(child)
