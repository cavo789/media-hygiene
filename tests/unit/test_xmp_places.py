"""The location fields of a sidecar: filled, kept when not ours, taken back."""

from __future__ import annotations

from typing import Final

from media_hygiene.tags.models import PlaceKind, Tag, TagSource
from media_hygiene.tags.xmp_doc import parse
from media_hygiene.tags.xmp_merge import XmpValues, merge, new_document
from media_hygiene.tags.xmp_owner import written_by_us
from media_hygiene.tags.xmp_places import (
    CITY,
    COUNTRY,
    LOCATION,
    NO_PLACES,
    XmpPlaces,
    places_of,
    simple_value,
)
from tests.support.sidecars import LIGHTROOM

_TOOL: Final = "media-hygiene 9.9"
_TURIN: Final = XmpPlaces("Turin", "Italy", "Chez Marco")
_WORDS: Final = ("Chez Marco", "Turin", "Italy")
# Lightroom writes simple properties as attributes of `rdf:Description`.
_LIGHTROOM_CITY: Final = LIGHTROOM.replace(
    '   crs:Exposure2012="+0.35">',
    '   xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"\n'
    '   photoshop:City="Torino"\n'
    '   crs:Exposure2012="+0.35">',
)


def _fields(data: bytes) -> tuple[str, str, str]:
    """Read the three fields back from the bytes written."""
    doc = parse(data)
    return (
        simple_value(doc, CITY),
        simple_value(doc, COUNTRY),
        simple_value(doc, LOCATION),
    )


def test_a_new_sidecar_gets_the_three_fields() -> None:
    """City, Country, Location; still ours alone; a rerun changes nothing."""
    doc = new_document(XmpValues(_WORDS, "", _TURIN), _TOOL)
    data = doc.to_bytes()
    assert _fields(data) == ("Turin", "Italy", "Chez Marco")
    assert b"<photoshop:City>Turin</photoshop:City>" in data
    assert b"<Iptc4xmpCore:Location>Chez Marco</Iptc4xmpCore:Location>" in data
    assert written_by_us(parse(data))
    assert not merge(parse(data), XmpValues(_WORDS, "", _TURIN))


def test_another_applications_city_is_kept() -> None:
    """Lightroom's City stays (attribute form); the empty Country is filled."""
    doc = parse(_LIGHTROOM_CITY.encode())
    assert merge(doc, XmpValues(_WORDS, "", _TURIN))
    data = doc.to_bytes()
    assert _fields(data) == ("Torino", "Italy", "Chez Marco")
    assert not merge(parse(data), XmpValues(_WORDS, "", _TURIN))


def test_ours_follows_the_tags_and_a_removed_one_stays_removed() -> None:
    """A new town replaces ours; one removed elsewhere is not written again."""
    doc = new_document(XmpValues(_WORDS, "", _TURIN), _TOOL)
    assert merge(doc, XmpValues(_WORDS, "", XmpPlaces("Moncalieri", "Italy")))
    assert _fields(doc.to_bytes()) == ("Moncalieri", "Italy", "")
    home = doc.descriptions()[0]
    city = home.find(CITY)
    assert city is not None
    home.remove(city)  # removed in another application
    assert not merge(doc, XmpValues(_WORDS, "", XmpPlaces("Moncalieri", "Italy")))
    assert _fields(doc.to_bytes()) == ("", "Italy", "")
    assert merge(doc, XmpValues((), ""))
    assert _fields(doc.to_bytes()) == ("", "", "")


def test_places_of_takes_the_first_of_each_kind() -> None:
    """Words of an older run (no kind) and other sources fill nothing."""
    tags = (
        Tag(TagSource.PLACE, "Maison"),
        Tag(TagSource.FOLDER, "Turin"),
        Tag(TagSource.PLACE, "Chez Marco", kind=PlaceKind.PERSONAL),
        Tag(TagSource.PLACE, "Plage", kind=PlaceKind.PERSONAL),
        Tag(TagSource.PLACE, "Turin", kind=PlaceKind.TOWN),
        Tag(TagSource.PLACE, "Italy", kind=PlaceKind.COUNTRY),
    )
    assert places_of(tags) == _TURIN
    assert places_of(tags[:2]) is NO_PLACES
