"""What a Google Photos Takeout `.json` says of its photo: date, place, description.

Fields read, as the tools handling Takeouts name them (not checked on a real one):
`photoTakenTime.timestamp` (Unix seconds, written as text), `geoData.latitude` and
`longitude` (0.0 when unknown), `description`. Facts only: the photo itself is never
written to.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

# A Takeout `.json` holds a few hundred bytes: a larger file is something else.
MAX_JSON_BYTES: Final = 1_000_000
_UNKNOWN: Final = 0.0  # both degrees at 0.0: no position
_MAX_LATITUDE: Final = 90.0
_MAX_LONGITUDE: Final = 180.0


@dataclass(frozen=True, slots=True)
class TakeoutFacts:
    """The date (Unix seconds), the position and the description Google recorded."""

    taken_at: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None

    @property
    def located(self) -> bool:
        """Tell whether Google recorded where the photo was taken.

        Returns:
            True with a latitude and a longitude.
        """
        return self.latitude is not None and self.longitude is not None


def read_takeout(path: Path) -> TakeoutFacts | None:
    """Read a Takeout `.json`.

    Args:
        path: The `.json` file.

    Returns:
        Its facts, or None when it cannot be read or is no Takeout `.json`.
    """
    try:
        if path.stat().st_size > MAX_JSON_BYTES:
            return None
        document = json.loads(path.read_bytes())
    except OSError, ValueError:
        return None
    return facts_of(document) if isinstance(document, dict) else None


def facts_of(document: dict[str, object]) -> TakeoutFacts:
    """Take the facts out of a Takeout document.

    Args:
        document: The parsed `.json`.

    Returns:
        What it holds; a missing or odd field is left unknown.
    """
    taken = document.get("photoTakenTime")
    stamp = taken.get("timestamp") if isinstance(taken, dict) else None
    place = document.get("geoData")
    latitude = _degrees(place, "latitude", _MAX_LATITUDE)
    longitude = _degrees(place, "longitude", _MAX_LONGITUDE)
    if latitude is None or longitude is None or latitude == longitude == _UNKNOWN:
        latitude = longitude = None
    description = document.get("description")
    return TakeoutFacts(
        taken_at=_seconds(stamp),
        latitude=latitude,
        longitude=longitude,
        description=description.strip() or None
        if isinstance(description, str)
        else None,
    )


def _seconds(stamp: object) -> int | None:
    """Read a Unix time written as text or as a number.

    Args:
        stamp: The field's value.

    Returns:
        The seconds, or None (missing, odd, or 0: no date).
    """
    if isinstance(stamp, bool) or not isinstance(stamp, str | int):
        return None
    try:
        seconds = int(stamp)
    except ValueError:
        return None
    return seconds if seconds > 0 else None


def _degrees(place: object, name: str, limit: float) -> float | None:
    """Read a latitude or a longitude.

    Args:
        place: The `geoData` object.
        name: `latitude` or `longitude`.
        limit: The largest value in degrees.

    Returns:
        The degrees, or None.
    """
    value = place.get(name) if isinstance(place, dict) else None
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    if abs(value) > limit:
        return None
    return float(value)
