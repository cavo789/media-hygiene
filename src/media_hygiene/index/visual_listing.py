"""The visual facts the index keeps of the library's images (`import`, 0245).

Read once, in one query: a file of a backup folder is left out, as are the images
never decoded (no hash).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.index.rows import visual_of
from media_hygiene.paths.host_paths import is_within

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.scan.models import VisualFacts

_VISUALS: Final = (
    "SELECT path, dhash, phash, width, height, sharpness, taken_at, camera"
    " FROM files WHERE dhash IS NOT NULL AND phash IS NOT NULL"
)


def library_visuals(
    connection: sqlite3.Connection, backups: tuple[Path, ...]
) -> tuple[VisualFacts, ...]:
    """Every image of the library the index describes.

    Args:
        connection: The index.
        backups: The backup folders: their images are not the library.

    Returns:
        Their visual facts.
    """
    found: list[VisualFacts] = []
    for path, *columns in connection.execute(_VISUALS):
        if any(is_within(Path(path), folder) for folder in backups):
            continue
        visual = visual_of(columns)
        if visual is not None:
            found.append(visual)
    return tuple(found)
