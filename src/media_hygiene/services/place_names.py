"""The names OpenStreetMap gave the places of new photos (0474), kept in the cache.

After an `import`, the new photos' positions are rounded (`geo.reverse.rounded`) and
grouped: one spot per group, never one per photo; a spot inside one of the user's
places, or already asked, is not asked again. The names are kept in
`<cache>/place-names.json` (an empty name too: asked once); the slideshow reads them
(`services.slideshow_places`). Nothing is sent here: `cli.import_places` asks first.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from PIL import Image, UnidentifiedImageError

from media_hygiene.classify.place_match import place_at, zones_of
from media_hygiene.geo.distance import Point
from media_hygiene.geo.reverse import rounded
from media_hygiene.scan.gps import exif_position

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.geo.reverse import ReverseLookup
    from media_hygiene.services.runtime import Runtime

type Spot = tuple[float, float]
PLACE_NAMES_FILE: Final = "place-names.json"
_ENCODING: Final = "utf-8"


def spot_key(spot: Spot) -> str:
    """How a spot is written in the file.

    Args:
        spot: A rounded position.

    Returns:
        E.g. `50.865,5.832`.
    """
    return f"{spot[0]},{spot[1]}"


def read_names(cache_dir: Path) -> dict[str, str]:
    """The names already asked.

    Args:
        cache_dir: The cache folder.

    Returns:
        Each spot's name by `spot_key`; empty when there is no file or it is damaged.
    """
    try:
        found = json.loads((cache_dir / PLACE_NAMES_FILE).read_text(_ENCODING))
    except OSError, ValueError:
        return {}
    if not isinstance(found, dict):
        return {}
    return {key: name for key, name in found.items() if isinstance(name, str)}


def photo_points(paths: Iterable[Path]) -> list[Point]:
    """The GPS positions of photos, read from their EXIF (videos have none here).

    Args:
        paths: The photos.

    Returns:
        The positions found.
    """
    points: list[Point] = []
    for path in paths:
        try:
            with Image.open(path) as image:
                position = exif_position(image.getexif())
        except OSError, UnidentifiedImageError, ValueError:
            continue
        if position is not None:
            points.append(Point(position.latitude, position.longitude))
    return points


def unnamed_spots(runtime: Runtime, points: Iterable[Point]) -> tuple[Spot, ...]:
    """The spots worth asking: not in a user's place, not asked before.

    Args:
        runtime: Settings (`[[classify.places]]`) and the cache folder.
        points: The new photos' positions.

    Returns:
        The rounded spots, each once, in a stable order.
    """
    zones = zones_of(runtime.settings.classify.places)
    known = read_names(runtime.locations.cache_dir)
    spots = {rounded(point) for point in points if place_at(point, zones) is None}
    return tuple(sorted(spot for spot in spots if spot_key(spot) not in known))


def name_spots(runtime: Runtime, spots: Iterable[Spot], lookup: ReverseLookup) -> int:
    """Ask a name for each spot, keep the answers, even when a request fails.

    Args:
        runtime: The cache folder.
        spots: The spots the user agreed to send.
        lookup: The online lookup.

    Returns:
        How many spots got a name.

    Raises:
        OSError: The service is unreachable or refused: the names found so far are kept.
    """
    names = read_names(runtime.locations.cache_dir)
    found = 0
    try:
        for spot in spots:
            name = lookup.name_at(spot)
            names[spot_key(spot)] = name
            found += bool(name)
    finally:
        _write(runtime.locations.cache_dir, names)
    return found


def _write(cache_dir: Path, names: Mapping[str, str]) -> None:
    """Write the names, atomically.

    Args:
        cache_dir: The cache folder.
        names: Each spot's name.
    """
    target = cache_dir / PLACE_NAMES_FILE
    draft = target.with_suffix(".tmp")
    draft.write_text(json.dumps(names, ensure_ascii=False, indent=1), _ENCODING)
    draft.replace(target)
