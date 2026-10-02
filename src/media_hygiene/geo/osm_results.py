"""Read Nominatim's answer: the areas found, each with its outline and its OSM id.

Only outlines (`Polygon`, `MultiPolygon`) make a place: a point or a road has no
inside. An outline of more than `areas.MAX_POINTS` points (a region, a country) is
counted but not listed: a `trip` rule names countries better.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.geo.areas import MAX_POINTS, check_shape

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.geo.areas import Polygon, Position, Ring, Shape

DECIMALS: Final = 5  # about 1 m
_KINDS: Final = ("addresstype", "type", "category")


class Geometry(StrEnum):
    """The GeoJSON outlines that make an area."""

    POLYGON = "Polygon"
    MULTIPOLYGON = "MultiPolygon"


@dataclass(frozen=True, slots=True)
class OsmArea:
    """One area found: what the page lists, draws, and saves."""

    osm: str  # e.g. "R1234567"
    name: str
    label: str  # the full name: village, municipality, province, country
    kind: str  # e.g. "village", "park"
    latitude: float
    longitude: float
    area: Shape


@dataclass(frozen=True, slots=True)
class Found:
    """The areas found, and how many outlines were too detailed to be listed."""

    areas: tuple[OsmArea, ...]
    too_large: int = 0


def read_results(payload: object) -> Found:
    """Read the JSON of a `/search` answer (`format=jsonv2`, `polygon_geojson=1`).

    Args:
        payload: The decoded JSON.

    Returns:
        The areas, in Nominatim's order (the most relevant first).

    Raises:
        TypeError: The answer is not a list of results.
    """
    if not isinstance(payload, list):
        message = "the answer is not a list of results"
        raise TypeError(message)
    areas: list[OsmArea] = []
    too_large = 0
    for row in payload:
        geojson = row.get("geojson") if isinstance(row, dict) else None
        if not isinstance(geojson, dict) or geojson.get("type") not in set(Geometry):
            continue  # a point or a line: no inside
        try:
            areas.append(_area(row, geojson))
        except _TooDetailedError:
            too_large += 1
        except KeyError, TypeError, ValueError, IndexError:
            continue  # a result Nominatim did not fill: skipped
    return Found(tuple(areas), too_large)


class _TooDetailedError(ValueError):
    """An outline of more than `MAX_POINTS` points."""


def _area(row: dict[str, object], geojson: dict[str, object]) -> OsmArea:
    """One result with an outline.

    Args:
        row: The result.
        geojson: Its outline.

    Returns:
        The area.

    Raises:
        _TooDetailedError: The outline has more than `MAX_POINTS` points.
        KeyError: A field is missing.
        TypeError: A field has another type.
        ValueError: The outline is invalid.
    """
    coordinates = geojson["coordinates"]
    if not isinstance(coordinates, list):
        raise TypeError(coordinates)
    multiple = geojson["type"] == Geometry.MULTIPOLYGON
    polygons = coordinates if multiple else [coordinates]
    shape = tuple(_polygon(polygon) for polygon in polygons)
    if sum(len(ring) for polygon in shape for ring in polygon) > MAX_POINTS:
        raise _TooDetailedError
    check_shape(shape)
    label = str(row["display_name"])
    kind = next((str(row[key]) for key in _KINDS if row.get(key)), "")
    return OsmArea(
        osm=f"{str(row['osm_type'])[:1].upper()}{int(str(row['osm_id']))}",
        name=str(row.get("name") or label.split(",", maxsplit=1)[0]).strip(),
        label=label,
        kind=kind,
        latitude=round(float(str(row["lat"])), DECIMALS),
        longitude=round(float(str(row["lon"])), DECIMALS),
        area=shape,
    )


def _polygon(rings: Sequence[Sequence[Sequence[float]]]) -> Polygon:
    """A GeoJSON polygon as `(latitude, longitude)` rings, without closing points.

    Args:
        rings: Its rings of `[longitude, latitude]` positions.

    Returns:
        The polygon.
    """
    return tuple(_ring(ring) for ring in rings)


def _ring(ring: Sequence[Sequence[float]]) -> Ring:
    """A GeoJSON ring as `(latitude, longitude)` positions.

    Args:
        ring: Its `[longitude, latitude]` positions, the last repeating the first.

    Returns:
        The ring, rounded to about a metre, the closing position dropped.
    """
    positions: list[Position] = [
        (round(float(lat), DECIMALS), round(float(lon), DECIMALS))
        for lon, lat, *_rest in ring
    ]
    if len(positions) > 1 and positions[0] == positions[-1]:
        positions.pop()
    return tuple(positions)
