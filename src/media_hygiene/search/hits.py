"""A file found, with its words: those of the index, and the people on it."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.search.exif_facts import exif_lines, taken_text
from media_hygiene.search.folder_order import kind_of_path
from media_hygiene.search.heaviest import video_facts
from media_hygiene.search.models import Hit
from media_hygiene.search.spot_label import spot_labels
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.index.tag_rows import TagStore
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.models import Found


# The words given at each search, never stored in the index: by file, by source.
type Given = dict[Path, dict[TagSource, tuple[str, ...]]]
_METADATA: Final = (
    "SELECT rowid, metadata, media_date FROM files WHERE rowid IN ({marks})"
)


def hit_of(
    words: tuple[TagStore | None, Mapping[Path, Mapping[TagSource, tuple[str, ...]]]],
    row: tuple[object, ...],
) -> Hit:
    """Make a hit of a row, with the tags of the file.

    Args:
        words: The tags of the index (None without any), and those given at
            each search (the people's names, the words typed by hand).
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
    for source, values in people.get(photo.path, {}).items():
        tags[source] = list(values)
    date = str(taken) if taken else None  # `YYYY-MM-DD`, from `media_day`
    return Hit(
        int(str(key)),
        photo,
        date,
        {source: tuple(values) for source, values in tags.items()},
    )


def given_too(
    given: Given, source: TagSource, words: Mapping[Path, tuple[str, ...]]
) -> Given:
    """The words given at each search, those of one source replaced.

    Args:
        given: The words given until now.
        source: The source replaced: `person` or `hand`.
        words: Its words, by file.

    Returns:
        The new words given.
    """
    fresh: Given = {}
    for path, sources in given.items():
        kept = {key: value for key, value in sources.items() if key is not source}
        if kept:
            fresh[path] = kept
    for path, values in words.items():
        if values:
            fresh.setdefault(path, {})[source] = tuple(values)
    return fresh


def with_facts(index: SearchIndex, found: Found) -> Found:
    """The files found with their metadata: when taken, EXIF, a video's length (0408).

    Read for the files shown only; an index older than the metadata gives none.

    Args:
        index: The open index.
        found: What a search found.

    Returns:
        The same files, described: the videos as the folder view does, every file
        with its date taken and its EXIF lines (0433), each video's seconds (0434).
    """
    if not found.hits:
        return found
    marks = ", ".join("?" * len(found.hits))
    try:
        rows = index.connection.execute(
            _METADATA.format(marks=marks), [hit.key for hit in found.hits]
        ).fetchall()
    except sqlite3.OperationalError:  # no `metadata` column: an older index
        return found
    known = {key: (json.loads(text) if text else {}, day) for key, text, day in rows}
    labels = spot_labels(
        index.connection, [hit.key for hit in found.hits], index.spot_names
    )
    hits = tuple(
        replace(_described(hit, known.get(hit.key)), spot=labels.get(hit.key, ""))
        for hit in found.hits
    )
    return replace(found, hits=hits)


def _described(hit: Hit, known: tuple[dict[str, object], str | None] | None) -> Hit:
    """One file with what its metadata says.

    Args:
        hit: The file.
        known: Its metadata and its date as written, None when the index has no row.

    Returns:
        The file described.
    """
    if known is None:
        return hit
    metadata, written = known
    taken = taken_text(written)
    video = kind_of_path(str(hit.photo.path)) == "videos"
    seconds = metadata.get("duration") if video else None
    return replace(
        hit,
        facts=video_facts(metadata) if video and metadata else "",
        taken=taken,
        exif=exif_lines(metadata, taken),
        seconds=float(seconds) if isinstance(seconds, int | float) else None,
    )
