"""The photos a place given may suit too: same day, same folder (0554).

Never placed here: `POST /api/place` names them, the page shows them as tiles, and only
those the user leaves picked are given, as any other. A photo with a position, a place
or set aside is not proposed, nor one whose day is not known: a day is what ties them.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.search.days import media_day
from media_hygiene.search.sidecar_days import days_of

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Collection

    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.query import SearchQuery

_ROWS: Final = "SELECT rowid, path, media_date FROM files"


def neighbours(
    connection: sqlite3.Connection, given: Collection[Path], out: Collection[Path]
) -> dict[Path, int]:
    """The keys of the other photos of the same day and folder as those given.

    One read of the index; the sidecars of the undated files of these folders only.

    Args:
        connection: The open index.
        given: The photos just given a place.
        out: Those never proposed: located, or placed.

    Returns:
        Each photo and its key, by path.
    """
    folders = {path.parent for path in given}
    rows = [
        (int(key), Path(written), day)
        for key, written, day in connection.execute(_ROWS)
        if Path(written).parent in folders
    ]
    known = days_of(path for _key, path, day in rows if media_day(day) is None)
    day_of = {path: media_day(day) or known.get(path) for _key, path, day in rows}
    spots = {(path.parent, day_of[path]) for path in given if day_of.get(path)}
    return dict(
        sorted(
            (path, key)
            for key, path, _day in rows
            if (path.parent, day_of[path]) in spots and path not in out
        )
    )


def among(index: SearchIndex, query: SearchQuery, keys: tuple[int, ...]) -> SearchQuery:
    """Keep a search to the photos of these keys.

    Args:
        index: The index.
        query: The search.
        keys: The keys, from the page.

    Returns:
        The search, narrowed.
    """
    paths = {str(found.path) for key in keys if (found := index.source_of(key))}
    return replace(query, filters=replace(query.filters, only=tuple(sorted(paths))))
