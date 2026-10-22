"""What an album's page shows on a phone (0297): its cover, dates, place and days.

Read from the index alone: each photo's sharpness (the audit's Laplacian) and its GPS
position (named offline, `geo/`). The cover is the sharpest photo of the first day; each
day is named after the town most of its photos were taken in. A video keeps its
address only when the phone's browser plays it as it is (`slideshow.films`), else its
format is said, as on the TV (0292).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import groupby
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.classify.whereabouts import located_point
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.slideshow.films import film_path
from media_hygiene.slideshow.pictures import thumb_path, tv_path

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable, Iterable

    from media_hygiene.geo.distance import Point
    from media_hygiene.services.slideshow_pick import Picked
    from media_hygiene.slideshow.slides import Slide

    type TownOf = Callable[[Point], str | None]

_FACTS: Final = "SELECT sharpness, metadata FROM files WHERE rowid = ?"


@dataclass(frozen=True, slots=True)
class Facts:
    """What the index knows of a photo for its album: sharpness, position."""

    sharpness: float | None = None
    point: Point | None = None


@dataclass(frozen=True, slots=True)
class AlbumSeen:
    """An album as the page shows it: its name, its photos, those missing."""

    name: str
    picked: Picked


def facts_of(connection: sqlite3.Connection, key: int) -> Facts:
    """Read a photo's sharpness and position from the index.

    Args:
        connection: The open index.
        key: The photo's key.

    Returns:
        Its facts; empty ones for an unknown key or unreadable metadata.
    """
    row = connection.execute(_FACTS, (key,)).fetchone()
    if row is None:
        return Facts()
    sharpness, text = row
    metadata = None
    if isinstance(text, str):
        try:
            metadata = MediaMetadata.model_validate_json(text)
        except ValidationError:
            metadata = None
    return Facts(sharpness, located_point(metadata))


def album_view(
    seen: AlbumSeen, connection: sqlite3.Connection, town_of: TownOf
) -> dict[str, object]:
    """Write an album for its page: cover, dates, place, then its photos by day.

    Args:
        seen: The album and its photos, oldest first.
        connection: The open index.
        town_of: Names the town of a position, or None.

    Returns:
        The JSON object: `name`, `count`, `missing`, `first`, `last`, `place`,
        `cover` (`thumb`, `photo`, or None) and `days` (`day`, `place`, `items`).
    """
    slides = seen.picked.slides
    facts = {slide.key: facts_of(connection, slide.key) for slide in slides}
    days = [
        (day or "", tuple(group))
        for day, group in groupby(slides, key=lambda slide: slide.day)
    ]
    dated = [day for day, _group in days if day]
    towns = [
        _commonest(town_of, (facts[slide.key].point for slide in group))
        for _day, group in days
    ]
    shown = [town for town in towns if town]
    return {
        "name": seen.name,
        "count": len(slides),
        "missing": seen.picked.missing,
        "first": dated[0] if dated else "",
        "last": dated[-1] if dated else "",
        "place": Counter(shown).most_common(1)[0][0] if shown else "",
        "cover": _cover(days[0][1] if days else (), facts) or _cover(slides, facts),
        "days": [
            {"day": day, "place": town or "", "items": [_item(s) for s in group]}
            for (day, group), town in zip(days, towns, strict=True)
        ],
    }


def _item(slide: Slide) -> dict[str, object]:
    """One photo or video of the mosaic.

    Args:
        slide: The photo or the video.

    Returns:
        Its key, thumbnail, phone-sized picture, video address and format.
    """
    film = slide.film
    return {
        "key": slide.key,
        "thumb": "" if film else thumb_path(slide.key),
        "photo": "" if film else tv_path(slide.key),
        "film": film_path(slide),
        "format": "" if film is None else film.label,
    }


def _cover(
    slides: tuple[Slide, ...], facts: dict[int, Facts]
) -> dict[str, object] | None:
    """The cover: the sharpest of these photos (the first day's), else the first one.

    Args:
        slides: The photos and videos of the first day (or of the album).
        facts: Each one's sharpness.

    Returns:
        Its key, thumbnail and picture addresses; None for videos only.
    """
    photos = [slide for slide in slides if slide.film is None]
    if not photos:
        return None
    best = max(photos, key=lambda slide: facts[slide.key].sharpness or 0.0)
    return {"key": best.key, "thumb": thumb_path(best.key), "photo": tv_path(best.key)}


def _commonest(town_of: TownOf, points: Iterable[Point | None]) -> str | None:
    """The town most of the positions lie in.

    Args:
        town_of: Names the town of a position.
        points: The positions; None for a photo without GPS.

    Returns:
        Its name; None when no position names a town.
    """
    towns = Counter(
        town for point in points if point is not None and (town := town_of(point))
    )
    return towns.most_common(1)[0][0] if towns else None
