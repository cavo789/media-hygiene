"""A GPS position in a sidecar, for a photo without one: its folder's town (0230).

Written as XMP-exif (`exif:GPSLatitude`, `exif:GPSLongitude`, in the XMP form
`48,5.7252N`), the way exiftool, digiKam or darktable read a position from a sidecar.
Like the location fields (`xmp_places`), what this tool wrote is remembered in `mh:`:
a position another application wrote is never replaced, and ours removed there is not
written again.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.tags.xmp_doc import EXIF_NS, MH_NS, text_of
from media_hygiene.tags.xmp_places import simple_value

if TYPE_CHECKING:
    from media_hygiene.geo.distance import Point
    from media_hygiene.tags.xmp_doc import XmpDoc

LATITUDE: Final = f"{{{EXIF_NS}}}GPSLatitude"
LONGITUDE: Final = f"{{{EXIF_NS}}}GPSLongitude"
VERSION: Final = f"{{{EXIF_NS}}}GPSVersionID"
_TRACKED: Final = f"{{{MH_NS}}}gps"
_GPS_VERSION: Final = "2.2.0.0"
_MINUTES: Final = 60
_DECIMALS: Final = 4  # a minute / 10,000: about 20 cm


@dataclass(frozen=True, slots=True)
class XmpGps:
    """A position, as the sidecar holds it."""

    latitude: str  # `48,5.7252N`
    longitude: str  # `4,19.7424W`

    @property
    def text(self) -> str:
        """Both coordinates, as remembered in `mh:gps`.

        Returns:
            `48,5.7252N 4,19.7424W`.
        """
        return f"{self.latitude} {self.longitude}"


def gps_of(point: Point) -> XmpGps:
    """Write a position in the XMP form.

    Args:
        point: Degrees, north and east positive.

    Returns:
        Its coordinates.
    """
    return XmpGps(coordinate(point.latitude, "NS"), coordinate(point.longitude, "EW"))


def coordinate(degrees: float, signs: str) -> str:
    """One coordinate in the XMP form `DDD,MM.mmmmK`.

    Args:
        degrees: The value, positive north or east.
        signs: The letters for positive then negative values (`NS`, `EW`).

    Returns:
        E.g. `48,5.7252N`.
    """
    sign = signs[0] if degrees >= 0 else signs[1]
    minutes = round(abs(degrees) * _MINUTES, _DECIMALS)
    whole, rest = divmod(minutes, _MINUTES)
    return f"{int(whole)},{rest:.{_DECIMALS}f}{sign}"


def merge_gps(doc: XmpDoc, gps: XmpGps | None) -> None:
    """Write (or take back) our position, in place.

    Args:
        doc: The sidecar.
        gps: Our position of today; None takes ours back.
    """
    current = gps_snapshot(doc)[0]
    tracked = text_of(doc.find(_TRACKED))
    value = gps.text if gps is not None else ""
    # Another application's position, or ours removed there, is kept.
    if current != tracked or current == value:
        return
    for each in doc.descriptions():
        for name in (LATITUDE, LONGITUDE, VERSION, _TRACKED):
            each.attrib.pop(name, None)
            for child in each.findall(name):
                each.remove(child)
    if gps is None:
        return
    home = doc.descriptions()[0]
    for name, text in (
        (VERSION, _GPS_VERSION),
        (LATITUDE, gps.latitude),
        (LONGITUDE, gps.longitude),
        (_TRACKED, gps.text),
    ):
        ET.SubElement(home, name).text = text


def gps_snapshot(doc: XmpDoc) -> tuple[str, str]:
    """The position of a sidecar and what this tool remembers of it.

    Args:
        doc: The sidecar.

    Returns:
        `latitude longitude` (empty without a position), then ours.
    """
    found = f"{simple_value(doc, LATITUDE)} {simple_value(doc, LONGITUDE)}".strip()
    return found, text_of(doc.find(_TRACKED))
