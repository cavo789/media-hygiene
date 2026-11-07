"""The landmark a photo shows, in its sidecar (0649): the truth the index caches.

`Iptc4xmpExt:LocationShown/Sublocation` holds the name, as digiKam and Lightroom read
it; `mh:landmark` remembers the one this tool wrote, so a name set by another
application is never replaced (the rule of `xmp_places`). The names the user said were
wrong go into the bag `mh:landmarksRejected`: they travel with the photo (sort, undo,
a folder renamed in Explorer) and are never proposed again.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Final

from media_hygiene.tags.xmp_bags import remove, set_list
from media_hygiene.tags.xmp_doc import (
    BAG,
    IPTC_EXT_NS,
    LI,
    MH_NS,
    RDF_NS,
    XmpDoc,
    items,
    text_of,
)
from media_hygiene.tags.xmp_merge import XmpValues, new_document

LOCATION_SHOWN: Final = f"{{{IPTC_EXT_NS}}}LocationShown"
SUBLOCATION: Final = f"{{{IPTC_EXT_NS}}}Sublocation"
_TRACKED: Final = f"{{{MH_NS}}}landmark"
_REJECTED: Final = f"{{{MH_NS}}}landmarksRejected"
_PARSE_TYPE: Final = f"{{{RDF_NS}}}parseType"


@dataclass(frozen=True, slots=True)
class SidecarLandmark:
    """What a sidecar says of the landmark: its name, ours or not, those rejected."""

    name: str = ""
    ours: bool = True  # empty, or written by this tool
    rejected: tuple[str, ...] = ()


def landmark_in(doc: XmpDoc) -> SidecarLandmark:
    """Read the landmark of a sidecar.

    Args:
        doc: The sidecar.

    Returns:
        Its name (the first location shown with a sublocation), and the rejected ones.
    """
    name = ""
    shown = doc.find(LOCATION_SHOWN)
    for entry in [] if shown is None else shown.iter(LI):
        name = (entry.get(SUBLOCATION) or text_of(entry.find(SUBLOCATION))).strip()
        if name:
            break
    ours = not name or name == text_of(doc.find(_TRACKED))
    return SidecarLandmark(name, ours, tuple(items(doc.find(_REJECTED))))


def with_landmark(doc: XmpDoc | None, name: str, tool: str) -> XmpDoc | None:
    """Name the landmark, or take ours back.

    Args:
        doc: The sidecar there; None: a new one.
        name: The name; empty takes ours back.
        tool: `media-hygiene <version>`, the creator of a new sidecar.

    Returns:
        The document changed; None when another application's name is there.
    """
    doc = new_document(XmpValues(()), tool) if doc is None else doc
    if not landmark_in(doc).ours:
        return None
    remove(doc, LOCATION_SHOWN)
    remove(doc, _TRACKED)
    if not name:
        return doc
    home = doc.descriptions()[0]
    bag = ET.SubElement(ET.SubElement(home, LOCATION_SHOWN), BAG)
    entry = ET.SubElement(bag, LI, {_PARSE_TYPE: "Resource"})
    ET.SubElement(entry, SUBLOCATION).text = name
    ET.SubElement(home, _TRACKED).text = name
    return doc


def with_rejected(doc: XmpDoc | None, name: str, tool: str) -> XmpDoc:
    """Remember a wrong name; take it off the photo when it is ours.

    Args:
        doc: The sidecar there; None: a new one.
        name: The name the user said is wrong.
        tool: `media-hygiene <version>`, the creator of a new sidecar.

    Returns:
        The document changed.
    """
    doc = new_document(XmpValues(()), tool) if doc is None else doc
    known = landmark_in(doc)
    if known.name.casefold() == name.casefold() and known.ours:
        with_landmark(doc, "", tool)
    if name.casefold() not in {each.casefold() for each in known.rejected}:
        set_list(doc, _REJECTED, [*known.rejected, name])
    return doc
