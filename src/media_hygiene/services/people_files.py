"""The photos `people` looks at: the pictures of the index, below the folders asked for.

No folder is walked: the photos are those the audits listed. Videos are left out (their
keyframes may come later), and so are the pictures an audit found broken.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.listing import indexed_files
from media_hygiene.paths.host_paths import is_within
from media_hygiene.report.thumbnails import PREVIEWABLE
from media_hygiene.scan.filters import media_kind
from media_hygiene.services.tag_files import require_index

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


def require_people_index(runtime: Runtime) -> None:
    """Refuse to run without an index: opening a missing one would create it empty.

    Args:
        runtime: Mount points.
    """
    require_index(
        runtime,
        (
            _("No index in {folder}: no photo to look at yet."),
            _(
                "Run 'audit' first with the same /cache mount: people reads the "
                "photos the audits listed, and keeps the faces there."
            ),
        ),
    )


def people_photos(
    connection: sqlite3.Connection, within: Sequence[Path]
) -> tuple[PhotoVersion, ...]:
    """The healthy pictures of the index, in path order.

    Args:
        connection: The open index.
        within: Container folders (`--path`); empty: every picture of the index.

    Returns:
        Their versions (path, size, mtime).
    """
    return tuple(
        PhotoVersion(file.path, file.size, file.mtime_ns)
        for file in indexed_files(connection)
        if media_kind(file.path) in PREVIEWABLE
        and file.facts.broken_reason is None
        and (not within or any(is_within(file.path, folder) for folder in within))
    )


def present_photos(
    photos: Iterable[PhotoVersion],
) -> tuple[tuple[PhotoVersion, ...], int]:
    """Keep the photos found on disk: a folder not mounted here holds none.

    Each folder is listed once, not each photo stat'ed: an index of a whole disk
    with one year mounted is sorted in a few hundred listings.

    Args:
        photos: The photos of the index.

    Returns:
        Those present, and how many are not.
    """
    listings: dict[Path, frozenset[str]] = {}
    present: list[PhotoVersion] = []
    absent = 0
    for photo in photos:
        folder = photo.path.parent
        if folder not in listings:
            listings[folder] = _names(folder)
        if photo.path.name in listings[folder]:
            present.append(photo)
        else:
            absent += 1
    return tuple(present), absent


def _names(folder: Path) -> frozenset[str]:
    """The names in a folder; none when it is missing or cannot be read.

    Args:
        folder: The folder.

    Returns:
        Its entries.
    """
    try:
        return frozenset(entry.name for entry in folder.iterdir())
    except OSError:
        return frozenset()
