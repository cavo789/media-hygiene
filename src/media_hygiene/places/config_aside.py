"""Write `[[places.ignored]]` into `config.toml`: the clusters set aside (0234).

A cluster not worth a name (two children in a car) is set aside with ✕: a circle around
its middle, so that a later audit moving the middle by a few metres still matches, and
two clusters in one circle go together. Restored, its circle leaves the file. Like the
folders (`config_folders`), the comments are kept and every answer is read back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import AoT

from media_hygiene.config.places_settings import IgnoredSpot
from media_hygiene.geo.distance import METRES_PER_KM, Point, distance_km
from media_hygiene.places.toml_edit import (
    DECIMALS,
    document_of,
    loaded,
    table_of,
    write_document,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_PLACES: Final = "places"
_IGNORED: Final = "ignored"


def read_aside(config_file: Path) -> tuple[IgnoredSpot, ...]:
    """The circles set aside, in their order in the file.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        Them.

    Raises:
        ValueError: The file or a circle is invalid.
    """
    rows = loaded(config_file).get(_PLACES, {}).get(_IGNORED, [])
    return tuple(IgnoredSpot.model_validate(row) for row in rows)


def aside_of(point: Point, spots: Sequence[IgnoredSpot]) -> int | None:
    """The first circle set aside that holds a cluster's middle.

    Args:
        point: The middle.
        spots: The circles.

    Returns:
        Its rank, or None.
    """
    for rank, spot in enumerate(spots):
        centre = Point(spot.latitude, spot.longitude)
        if distance_km(point, centre) * METRES_PER_KM <= spot.radius_m:
            return rank
    return None


def set_aside(config_file: Path, spot: IgnoredSpot) -> None:
    """Add a circle at the end of `[[places.ignored]]`.

    Args:
        config_file: `config.toml`, created when missing.
        spot: The circle.

    Raises:
        ValueError: The file is not TOML.
        OSError: The file cannot be written.
    """
    document = document_of(config_file)
    places = table_of(document, _PLACES)
    rows = places.get(_IGNORED)
    if not isinstance(rows, AoT):
        rows = tomlkit.aot()
        places.append(_IGNORED, rows)
    table = tomlkit.table()
    table["latitude"] = round(spot.latitude, DECIMALS)
    table["longitude"] = round(spot.longitude, DECIMALS)
    radius = spot.radius_m
    table["radius_m"] = int(radius) if radius.is_integer() else radius
    table.add(tomlkit.nl())  # a blank line before what follows
    rows.append(table)
    write_document(config_file, document)


def restore(config_file: Path, spot: IgnoredSpot) -> None:
    """Take the circles at a position out of the file.

    Args:
        config_file: `config.toml`.
        spot: The circle, as read back: matched by its position, not its rank, in
            case the file was edited by hand meanwhile.

    Raises:
        ValueError: The file is not TOML.
        OSError: The file cannot be written.
    """
    document = document_of(config_file)
    places = table_of(document, _PLACES)
    rows = places.get(_IGNORED)
    if not isinstance(rows, AoT):
        return
    at = (round(spot.latitude, DECIMALS), round(spot.longitude, DECIMALS))
    for rank in reversed(range(len(rows.body))):
        row = rows.body[rank]
        found = (
            round(float(row.get("latitude", 0)), DECIMALS),
            round(float(row.get("longitude", 0)), DECIMALS),
        )
        if found == at:
            del rows[rank]
    if not rows.body:
        del places[_IGNORED]
    write_document(config_file, document)
