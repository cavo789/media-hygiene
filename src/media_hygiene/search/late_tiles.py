"""The late files of an event as the search's tiles (0558), how each one fits it."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, cast

from media_hygiene.classify.late_files import Likely
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.hits import hit_of, with_facts
from media_hygiene.search.models import Found
from media_hygiene.search.views import found_view

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.classify.late_files import LateEvent
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.fts import SearchIndex

_ROW: Final = (
    f"SELECT rowid, path, size, mtime_ns, {DAY}(media_date) FROM files"  # noqa: S608
    " WHERE rowid = ?"
)
# Same camera first, then those to ask, then elsewhere, then another event's.
_ORDER: Final = (Likely.PROBABLY, Likely.ASK, Likely.ELSEWHERE, Likely.OTHER)


def late_tiles(
    index: SearchIndex,
    event: LateEvent,
    shown: tuple[HostPathMapper, frozenset[str], Mapping[str, str]],
) -> dict[str, object]:
    """The tiles of an event's late files, ranked by how they fit.

    Args:
        index: The open index.
        event: The event and its late files.
        shown: The host paths' mapper, the files set aside, rule name → label.

    Returns:
        `{total, hits}`, each hit with `likely`, `ticked` and `other` (a label).
    """
    mapper, chosen, names = shown
    files = sorted(event.files, key=lambda file: _ORDER.index(file.likely))
    execute = index.connection.execute
    rows = [(file, execute(_ROW, (file.key,)).fetchone()) for file in files]
    held = [(file, row) for file, row in rows if row is not None]
    hits = tuple(hit_of((None, {}), row) for _file, row in held)
    found = with_facts(index, Found(len(hits), hits))
    view = found_view(found, mapper, chosen)
    tiles = cast("list[dict[str, object]]", view["hits"])
    view["hits"] = [
        {
            **tile,
            "likely": file.likely.value,
            "ticked": file.likely is Likely.PROBABLY,
            "other": names.get(file.other, file.other),
        }
        for tile, (file, _row) in zip(tiles, held, strict=True)
    ]
    return view
