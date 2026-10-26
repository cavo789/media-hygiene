"""A file found, with its words: those of the index, and the people on it."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.search.folder_order import kind_of_path
from media_hygiene.search.heaviest import video_facts
from media_hygiene.search.models import Hit
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.index.tag_rows import TagStore
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.models import Found


_METADATA: Final = "SELECT rowid, metadata FROM files WHERE rowid IN ({marks})"


def hit_of(
    words: tuple[TagStore | None, Mapping[Path, tuple[str, ...]]],
    row: tuple[object, ...],
) -> Hit:
    """Make a hit of a row, with the tags of the file.

    Args:
        words: The tags of the index (None without any), and the people.
        row: Key, path, size, mtime and day (`YYYY-MM-DD`) of a file.

    Returns:
        The hit.
    """
    key, path, size, mtime_ns, taken = row
    photo = PhotoVersion(Path(str(path)), int(str(size)), int(str(mtime_ns)))
    store, people = words
    tags: dict[TagSource, list[str]] = {}
    for tag in store.of(photo) if store is not None else ():
        tags.setdefault(tag.source, []).append(tag.value)
    if photo.path in people:
        tags[TagSource.PERSON] = list(people[photo.path])
    date = str(taken) if taken else None  # `YYYY-MM-DD`, from `media_day`
    return Hit(
        int(str(key)),
        photo,
        date,
        {source: tuple(values) for source, values in tags.items()},
    )


def with_facts(index: SearchIndex, found: Found) -> Found:
    """The files found, each video with its length, bit rate and codec (0408).

    Read for the files shown only; an index older than the metadata gives none.

    Args:
        index: The open index.
        found: What a search found.

    Returns:
        The same files, the videos described as the folder view does.
    """
    videos = [
        hit for hit in found.hits if kind_of_path(str(hit.photo.path)) == "videos"
    ]
    if not videos:
        return found
    marks = ", ".join("?" * len(videos))
    try:
        rows = index.connection.execute(
            _METADATA.format(marks=marks), [hit.key for hit in videos]
        ).fetchall()
    except sqlite3.OperationalError:  # no `metadata` column: an older index
        return found
    facts = {key: video_facts(json.loads(text)) for key, text in rows if text}
    hits = tuple(replace(hit, facts=facts.get(hit.key, "")) for hit in found.hits)
    return replace(found, hits=hits)
