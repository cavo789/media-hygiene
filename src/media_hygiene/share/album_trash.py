"""The albums of the last delete, kept next to the albums file for *Undo* (0499).

The copy is forgotten after `KEEP_DAYS` days: an *Undo* weeks later would bring back
albums the user has long since forgotten deleting.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Final

from media_hygiene.share.albums import AlbumsFile, read_albums

if TYPE_CHECKING:
    from pathlib import Path

DELETED_FILE: Final = "albums-deleted.json"  # the last delete, for Undo
KEEP_DAYS: Final = 30  # a deleted album can be put back this long
_DAY_SECONDS: Final = 86_400


def deleted_path(albums_file: Path) -> Path:
    """Where the albums of the last delete are kept: next to the albums file.

    Args:
        albums_file: The albums file.

    Returns:
        The file.
    """
    return albums_file.with_name(DELETED_FILE)


def recent_deleted(albums_file: Path) -> AlbumsFile:
    """Read the albums of the last delete; a copy older than `KEEP_DAYS` is removed.

    Args:
        albums_file: The albums file.

    Returns:
        The albums to put back; none when there is no copy or it is too old.
    """
    path = deleted_path(albums_file)
    try:
        age = time.time() - path.stat().st_mtime
    except FileNotFoundError:
        return AlbumsFile()
    if age > KEEP_DAYS * _DAY_SECONDS:
        path.unlink(missing_ok=True)
        return AlbumsFile()
    return read_albums(path)
