"""Put our words into a sidecar without taking anything of anybody else's.

- `dc:subject` gets the words this tool produces, after those already there; the
  words it wrote last time (`mh:subjects`) and no longer produces are taken back, and
  a word it wrote that is gone (removed in another application) is not added again
  (`xmp_bags`). The names of the people go into `Iptc4xmpExt:PersonInImage` the same
  way, only when the user chose the `person` source.
- `dc:description` gets the model's sentence only when empty, or when it still holds
  the sentence this tool wrote last time (`mh:description`).
- The town, the country and the user's place go into the location fields: `xmp_places`.
- A position for a photo without one, from its folder's town: `xmp_gps` (0230).
- A new sidecar says who wrote it (`xmp:CreatorTool`): see `xmp_owner`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Final

from media_hygiene.tags import xmp_gps, xmp_places
from media_hygiene.tags.xmp_bags import merge_tracked, remove, tracked_snapshot
from media_hygiene.tags.xmp_doc import (
    ABOUT,
    ALT,
    DC_NS,
    DEFAULT_LANG,
    IPTC_EXT_NS,
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

SUBJECT: Final = f"{{{DC_NS}}}subject"
CAPTION: Final = f"{{{DC_NS}}}description"
CREATOR: Final = f"{{{XMP_NS}}}CreatorTool"
_MH_SUBJECTS: Final = f"{{{MH_NS}}}subjects"
_SUBJECTS: Final = (SUBJECT, _MH_SUBJECTS)
PERSON_IN_IMAGE: Final = f"{{{IPTC_EXT_NS}}}PersonInImage"
_PEOPLE: Final = (PERSON_IN_IMAGE, f"{{{MH_NS}}}people")
_MH_CAPTION: Final = f"{{{MH_NS}}}description"
_XPACKET_BEGIN: Final = '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
_XPACKET_END: Final = '\n<?xpacket end="w"?>\n'
_TOOLKIT: Final = f"{{{X_NS}}}xmptk"
_INDENT: Final = " "


@dataclass(frozen=True, slots=True)
class XmpValues:
    """What this tool writes for one file: words, sentence, place, people's names."""

    subjects: tuple[str, ...]
    description: str = ""
    places: xmp_places.XmpPlaces = xmp_places.NO_PLACES
    people: tuple[str, ...] = ()  # only with the `person` source: names travel
    gps: xmp_gps.XmpGps | None = None  # `xmp_folder_gps`: its folder's town (0230)


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
    xmp_gps.merge_gps(doc, values.gps)
    return _snapshot(doc) != before


def _snapshot(doc: XmpDoc) -> tuple[object, ...]:
    """The values `merge` may change.

    Args:
        doc: The sidecar.

    Returns:
        Its words and ours, its people and ours, its sentence and ours, its
        location fields and ours.
    """
    return (
        tracked_snapshot(doc, _SUBJECTS),
        tracked_snapshot(doc, _PEOPLE),
        _caption(doc),
        text_of(doc.find(_MH_CAPTION)),
        xmp_places.places_snapshot(doc),
        xmp_gps.gps_snapshot(doc),
    )


def _merge(doc: XmpDoc, values: XmpValues) -> None:
    """Merge our values into a sidecar, in place.

    Args:
        doc: The sidecar.
        values: Our words and sentence of today.
    """
    merge_tracked(doc, _SUBJECTS, values.subjects)
    merge_tracked(doc, _PEOPLE, values.people)
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
    remove(doc, CAPTION)
    remove(doc, _MH_CAPTION)
    if not sentence:
        return
    home = doc.descriptions()[0]
    alt = ET.SubElement(ET.SubElement(home, CAPTION), ALT)
    ET.SubElement(alt, LI, {LANG: DEFAULT_LANG}).text = sentence
    ET.SubElement(home, _MH_CAPTION).text = sentence
