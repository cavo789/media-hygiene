"""A file found, with its words: those of the index, and the people on it."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.search.models import Hit
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.index.tag_rows import TagStore

_DATE_LENGTH: Final = 10  # `YYYY:MM:DD`, then the time
_EXIF_SEPARATOR, _DATE_SEPARATOR = ":", "-"


def hit_of(
    words: tuple[TagStore | None, Mapping[Path, tuple[str, ...]]],
    row: tuple[object, ...],
) -> Hit:
    """Make a hit of a row, with the tags of the file.

    Args:
        words: The tags of the index (None without any), and the people.
        row: Key, path, size, mtime and date of a file.

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
    date = (
        str(taken)[:_DATE_LENGTH].replace(_EXIF_SEPARATOR, _DATE_SEPARATOR)
        if taken
        else None
    )
    return Hit(
        int(str(key)),
        photo,
        date,
        {source: tuple(values) for source, values in tags.items()},
    )
