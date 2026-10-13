"""The shape of an area, and the checks it must pass: no numpy, read with the settings.

Positions are `(latitude, longitude)` pairs, in the order of the rest of `config.toml`.
`geo.areas` builds the arrays that test points against a shape.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Iterable

type Position = tuple[float, float]
type Ring = tuple[Position, ...]
type Polygon = tuple[Ring, ...]  # the outer ring first, then its holes
type Shape = tuple[Polygon, ...]

MIN_RING: Final = 3  # a triangle; a closing point repeating the first is allowed
MAX_POINTS: Final = 1000  # beyond, a region or a country: a trip says it better
_MAX_LATITUDE: Final = 90
_MAX_LONGITUDE: Final = 180


def check_shape(shape: Shape) -> Shape:
    """Refuse an area that cannot be one.

    Args:
        shape: Its polygons.

    Returns:
        It, unchanged.

    Raises:
        ValueError: No polygon, a polygon without an outer ring, a ring of fewer than
            three points, a position off the Earth, or more than `MAX_POINTS` points.
    """
    if not shape or any(not polygon for polygon in shape):
        message = _("an area needs at least one polygon, each with an outer ring")
        raise ValueError(message)
    if any(len(set(ring)) < MIN_RING for ring in rings(shape)):
        message = _("a ring of an area needs at least {count} points").format(
            count=MIN_RING
        )
        raise ValueError(message)
    count = sum(len(ring) for ring in rings(shape))
    if count > MAX_POINTS:
        message = _(
            "an area of {count} points is too detailed (at most {limit})"
        ).format(count=count, limit=MAX_POINTS)
        raise ValueError(message)
    for latitude, longitude in (p for ring in rings(shape) for p in ring):
        if abs(latitude) > _MAX_LATITUDE or abs(longitude) > _MAX_LONGITUDE:
            message = _(
                "({latitude}, {longitude}) is not a position on the Earth"
            ).format(latitude=latitude, longitude=longitude)
            raise ValueError(message)
    return shape


def rings(shape: Shape) -> Iterable[Ring]:
    """Every ring of an area: outer rings and holes alike.

    Args:
        shape: Its polygons.

    Returns:
        The rings.
    """
    return (ring for polygon in shape for ring in polygon)
