"""Where a file was taken: EXIF GPS tags (photos) or an ISO 6709 string (videos).

A malformed or impossible position is ignored, never fatal. So is `0, 0`: devices write
it when they have no fix, and nobody photographs the Gulf of Guinea that often.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.exif_values import number

if TYPE_CHECKING:
    from PIL import Image

GPS_IFD: Final = 0x8825
_LATITUDE_REF, _LATITUDE, _LONGITUDE_REF, _LONGITUDE = 1, 2, 3, 4
_ALTITUDE_REF, _ALTITUDE = 5, 6
_MAX_LATITUDE: Final = 90.0
_MAX_LONGITUDE: Final = 180.0
_MINUTES: Final = 60.0
_BELOW_SEA_LEVEL: Final = 1
# Decimal degrees, as phones write it: `+48.8566+002.3522+035.0/`.
_ISO_6709: Final = re.compile(
    r"(?P<lat>[+-]\d+(?:\.\d+)?)(?P<lon>[+-]\d+(?:\.\d+)?)(?P<alt>[+-]\d+(?:\.\d+)?)?"
)


@dataclass(frozen=True, slots=True)
class Position:
    """A place on Earth: decimal degrees, and metres above sea level when known."""

    latitude: float
    longitude: float
    altitude: float | None = None


def exif_position(exif: Image.Exif) -> Position | None:
    """Read the GPS tags of an image.

    Args:
        exif: The image's EXIF.

    Returns:
        The position, or None when absent or malformed.
    """
    gps = exif.get_ifd(GPS_IFD)
    latitude = _coordinate(gps.get(_LATITUDE), gps.get(_LATITUDE_REF), "S")
    longitude = _coordinate(gps.get(_LONGITUDE), gps.get(_LONGITUDE_REF), "W")
    if latitude is None or longitude is None:
        return None
    return _checked(Position(latitude, longitude, _altitude(gps)))


def position_fields(position: Position | None) -> dict[str, object]:
    """Turn a position into metadata fields.

    Args:
        position: The position, or None.

    Returns:
        Latitude, longitude and altitude; nothing without a position.
    """
    if position is None:
        return {}
    return {
        "latitude": position.latitude,
        "longitude": position.longitude,
        "altitude": position.altitude,
    }


def iso6709_position(text: str | None) -> Position | None:
    """Read an ISO 6709 position, as videos store it.

    Args:
        text: The tag, e.g. `+48.8566+002.3522/`.

    Returns:
        The position, or None when absent or malformed.
    """
    found = _ISO_6709.match(text.strip()) if text else None
    if found is None:
        return None
    altitude = float(found["alt"]) if found["alt"] else None
    return _checked(Position(float(found["lat"]), float(found["lon"]), altitude))


def _checked(position: Position) -> Position | None:
    """Keep a position only when it is a real place.

    Args:
        position: A position read from a file.

    Returns:
        It, or None when out of range, not a number, or `0, 0`.
    """
    latitude, longitude = position.latitude, position.longitude
    if not (math.isfinite(latitude) and math.isfinite(longitude)):
        return None
    if abs(latitude) > _MAX_LATITUDE or abs(longitude) > _MAX_LONGITUDE:
        return None
    if latitude == 0 and longitude == 0:
        return None
    altitude = position.altitude
    if altitude is not None and not math.isfinite(altitude):
        return Position(latitude, longitude)
    return position


def _coordinate(value: object, ref: object, negative: str) -> float | None:
    """Turn degrees, minutes and seconds into signed decimal degrees.

    Args:
        value: One number, or up to three (degrees, minutes, seconds).
        ref: The hemisphere (`N`, `S`, `E` or `W`), as text or bytes.
        negative: The hemisphere that makes the value negative.

    Returns:
        The coordinate, or None when it cannot be read.
    """
    parts = value if isinstance(value, tuple | list) else (value,)
    numbers = [number(part) for part in parts[:3]]
    if not numbers or None in numbers:
        return None
    degrees = sum(
        part / _MINUTES**index for index, part in enumerate(numbers) if part is not None
    )
    hemisphere = ref.decode(errors="replace") if isinstance(ref, bytes) else str(ref)
    return -degrees if hemisphere.strip().upper() == negative else degrees


def _altitude(gps: dict[int, object]) -> float | None:
    """Read the altitude, below sea level when its reference says so.

    Args:
        gps: The GPS tags.

    Returns:
        Metres, or None when absent or unreadable.
    """
    metres = number(gps.get(_ALTITUDE))
    if metres is None:
        return None
    ref = gps.get(_ALTITUDE_REF)
    below = ref in {_BELOW_SEA_LEVEL, bytes([_BELOW_SEA_LEVEL])}
    return -metres if below else metres
