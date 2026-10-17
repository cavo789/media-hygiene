"""A position in a sidecar from the folder's town (0230): form, never over others."""

from __future__ import annotations

from typing import Final

import pytest

from media_hygiene.geo.distance import Point
from media_hygiene.tags.xmp_doc import parse
from media_hygiene.tags.xmp_gps import (
    LATITUDE,
    LONGITUDE,
    coordinate,
    gps_of,
    gps_snapshot,
)
from media_hygiene.tags.xmp_merge import XmpValues, merge, new_document
from media_hygiene.tags.xmp_places import simple_value
from tests.support.sidecars import LIGHTROOM

_TOOL: Final = "media-hygiene 9.9"
_DOUARNENEZ: Final = gps_of(Point(48.09542, -4.32904))
_LUZ: Final = gps_of(Point(43.38871, -1.66324))
# Lightroom writes a position of its own as attributes of `rdf:Description`.
_LIGHTROOM_GPS: Final = LIGHTROOM.replace(
    '   crs:Exposure2012="+0.35">',
    '   xmlns:exif="http://ns.adobe.com/exif/1.0/"\n'
    '   exif:GPSLatitude="47,0.0000N"\n'
    '   exif:GPSLongitude="2,0.0000E"\n'
    '   crs:Exposure2012="+0.35">',
)


@pytest.mark.parametrize(
    ("degrees", "signs", "written"),
    [
        (48.09542, "NS", "48,5.7252N"),
        (-4.32904, "EW", "4,19.7424W"),
        (0.0, "NS", "0,0.0000N"),
        (-0.5, "NS", "0,30.0000S"),
        (43.999999, "NS", "43,59.9999N"),
        (179.9999999, "EW", "180,0.0000E"),
    ],
)
def test_a_coordinate_in_the_xmp_form(degrees: float, signs: str, written: str) -> None:
    """`DDD,MM.mmmmK`: degrees, minutes to four decimals, then the hemisphere."""
    assert coordinate(degrees, signs) == written


def test_a_new_sidecar_gets_the_position_once() -> None:
    """Latitude, longitude, version; a rerun changes nothing."""
    data = new_document(XmpValues((), gps=_DOUARNENEZ), _TOOL).to_bytes()
    doc = parse(data)
    assert simple_value(doc, LATITUDE) == "48,5.7252N"
    assert simple_value(doc, LONGITUDE) == "4,19.7424W"
    assert b"<exif:GPSVersionID>2.2.0.0</exif:GPSVersionID>" in data
    assert not merge(doc, XmpValues((), gps=_DOUARNENEZ))


def test_another_applications_position_is_kept() -> None:
    """Lightroom's own position stays, whatever the town says."""
    doc = parse(_LIGHTROOM_GPS.encode())
    assert not merge(doc, XmpValues((), gps=_DOUARNENEZ))
    assert gps_snapshot(doc) == ("47,0.0000N 2,0.0000E", "")


def test_ours_follows_the_town_and_is_taken_back() -> None:
    """A new town moves ours; None (the setting off) takes it back."""
    doc = new_document(XmpValues((), gps=_DOUARNENEZ), _TOOL)
    assert merge(doc, XmpValues((), gps=_LUZ))
    assert simple_value(doc, LATITUDE) == _LUZ.latitude
    assert merge(doc, XmpValues(()))
    assert gps_snapshot(doc) == ("", "")


def test_ours_removed_elsewhere_is_not_written_again() -> None:
    """The user deleted our position in another application: it stays deleted."""
    doc = new_document(XmpValues((), gps=_DOUARNENEZ), _TOOL)
    for each in doc.descriptions():
        for name in (LATITUDE, LONGITUDE):
            for child in each.findall(name):
                each.remove(child)
    assert not merge(doc, XmpValues((), gps=_DOUARNENEZ))
    assert gps_snapshot(doc)[0] == ""
