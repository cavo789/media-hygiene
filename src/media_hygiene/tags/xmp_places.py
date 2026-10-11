"""Put the town, the country and the user's place into the location fields of a sidecar.

Photo managers (digiKam, Lightroom, Immich) show `photoshop:City`,
`photoshop:Country` and `Iptc4xmpCore:Location` apart from the keywords. Each one is
set only when empty or still holding the value this tool wrote last time (tracked in
`mh:`, as `dc:subject` is): a value set by another application is never replaced, and
a value of ours removed there is not written again.
A property may be written as an element or as an attribute of `rdf:Description`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.tags.models import PlaceKind, TagSource
from media_hygiene.tags.xmp_doc import IPTC_CORE_NS, MH_NS, PHOTOSHOP_NS, text_of

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.tags.models import Tag
    from media_hygiene.tags.xmp_doc import XmpDoc

CITY: Final = f"{{{PHOTOSHOP_NS}}}City"
COUNTRY: Final = f"{{{PHOTOSHOP_NS}}}Country"
LOCATION: Final = f"{{{IPTC_CORE_NS}}}Location"
# Each field, and where this tool remembers what it wrote into it.
_FIELDS: Final = (
    (CITY, f"{{{MH_NS}}}city"),
    (COUNTRY, f"{{{MH_NS}}}country"),
    (LOCATION, f"{{{MH_NS}}}location"),
)
PLACE_FIELDS: Final = frozenset(name for name, _ in _FIELDS)


@dataclass(frozen=True, slots=True)
class XmpPlaces:
    """Where the photo was taken, each field empty when not known."""

    city: str = ""  # the GeoNames town
    country: str = ""  # its country
    location: str = ""  # the first place of the user's


NO_PLACES: Final = XmpPlaces()


def places_of(tags: Sequence[Tag]) -> XmpPlaces:
    """The location fields of a file: its first town, country and personal place.

    Args:
        tags: Its tags; place words of an older `tags` run have no kind and fill
            nothing.

    Returns:
        The fields.
    """
    first: dict[PlaceKind, str] = {}
    for tag in tags:
        if tag.source is TagSource.PLACE:
            for kind in tag.kinds:
                first.setdefault(kind, tag.value)
    if not first:
        return NO_PLACES
    return XmpPlaces(
        first.get(PlaceKind.TOWN, ""),
        first.get(PlaceKind.COUNTRY, ""),
        first.get(PlaceKind.PERSONAL, ""),
    )


def merge_places(doc: XmpDoc, places: XmpPlaces) -> None:
    """Fill (or take back) the location fields, in place.

    Args:
        doc: The sidecar.
        places: Our values of today; an empty one takes ours back.
    """
    for (field, tracked), value in zip(
        _FIELDS, (places.city, places.country, places.location), strict=True
    ):
        current = simple_value(doc, field)
        # Another application's value, or ours removed there, is kept; ours is
        # rewritten only when it changes.
        if current != text_of(doc.find(tracked)) or current == value:
            continue
        _set(doc, (field, tracked), value)


def places_snapshot(doc: XmpDoc) -> tuple[str, ...]:
    """The values `merge_places` may change.

    Args:
        doc: The sidecar.

    Returns:
        Each field, then what this tool remembers of it.
    """
    return tuple(
        value
        for field, tracked in _FIELDS
        for value in (simple_value(doc, field), text_of(doc.find(tracked)))
    )


def simple_value(doc: XmpDoc, name: str) -> str:
    """The value of a simple property, written as an element or an attribute.

    Args:
        doc: The sidecar.
        name: The property (`{namespace}name`).

    Returns:
        Its text, stripped; empty without any.
    """
    for each in doc.descriptions():
        if (attribute := each.get(name)) is not None:
            return attribute.strip()
    return text_of(doc.find(name))


def _set(doc: XmpDoc, names: tuple[str, str], value: str) -> None:
    """Write (or take back) one field, and remember it.

    Args:
        doc: The sidecar.
        names: The field and where this tool remembers it.
        value: The value; empty takes ours back.
    """
    for each in doc.descriptions():
        for name in names:
            each.attrib.pop(name, None)
            for child in each.findall(name):
                each.remove(child)
    if not value:
        return
    home = doc.descriptions()[0]
    for name in names:
        ET.SubElement(home, name).text = value
