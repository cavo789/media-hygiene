"""The name the Events view proposes for an event (0477): from the index's tags.

The place words (`place` tags: a place of the user's first, else the town) and the
vision words of its photos, read in one query; the day is its first photo's.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from datetime import date
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.event_title import TitleFacts, activity_of, proposed_title
from media_hygiene.tags.models import PlaceKind, TagSource

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.search.models import Found

_TAGS: Final = (
    "SELECT path, source, value, kind FROM tags"
    " WHERE source IN (?, ?) AND path IN ({marks})"
)


def suggested(connection: sqlite3.Connection, found: Found) -> str:
    """Propose a name for the photos of an event.

    Args:
        connection: The open index.
        found: Its photos, as the search found them.

    Returns:
        « Walk in Liège », « Liège — 29 October », the day; empty without photos.
    """
    days = sorted(hit.date for hit in found.hits if hit.date)
    day = date.fromisoformat(days[0][:10]) if days else None
    return title_of(connection, [str(hit.photo.path) for hit in found.hits], day)


def title_of(
    connection: sqlite3.Connection, paths: Sequence[str], day: date | None
) -> str:
    """Propose a name for some files of the index.

    Args:
        connection: The open index.
        paths: Their container paths.
        day: Their first day, if known.

    Returns:
        The name proposed; empty without files.
    """
    if not paths:
        return ""
    try:
        rows = connection.execute(
            _TAGS.format(marks=", ".join("?" * len(paths))),
            [TagSource.PLACE.value, TagSource.VISION.value, *paths],
        ).fetchall()
    except sqlite3.OperationalError:  # an index older than the tags' kind
        rows = []
    words: dict[str, list[str]] = {}
    places: dict[str, Counter[str]] = {}
    for path, source, value, kind in rows:
        if source == TagSource.VISION.value:
            words.setdefault(path, []).append(value)
            continue
        for named in str(kind).split(","):
            places.setdefault(named, Counter())[value] += 1
    place = next(
        (
            places[kind.value].most_common(1)[0][0]
            for kind in (PlaceKind.PERSONAL, PlaceKind.TOWN)
            if kind.value in places
        ),
        "",
    )
    return proposed_title(TitleFacts(place, day, activity_of(words.values())))
