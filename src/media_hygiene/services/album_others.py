"""Another name of an album's link, among the files the index knows (0374).

The index lists the analysed folders (the album folder is skipped by every scan): a
file of the same size whose disk and inode are the link's is another name of the same
photo. Among several, the first path: the same answer every time.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.host_paths import is_within
from media_hygiene.share.album_follow import Lookup

if TYPE_CHECKING:
    import os
    import sqlite3
    from collections.abc import Callable

    from media_hygiene.services.runtime import Runtime

_SAME_SIZE: Final = "SELECT path FROM files WHERE size = ? ORDER BY path"


def find_other(
    connection: sqlite3.Connection | None, folder: Path
) -> Callable[[os.stat_result], Path | None]:
    """Make the finder of another name, outside the album folder.

    Args:
        connection: The index, or None (then no other name is ever found).
        folder: The album folder.

    Returns:
        The finder: a link's stat gives another name, or None.
    """

    def other_name(info: os.stat_result) -> Path | None:
        """Another name of the file `info` describes, or None.

        Args:
            info: The link's stat.

        Returns:
            The first path of the index that is the same file, outside the album.
        """
        if connection is None:
            return None
        rows = connection.execute(_SAME_SIZE, (info.st_size,)).fetchall()
        for (text,) in rows:
            path = Path(text)
            if is_within(path, folder):
                continue
            try:
                found = path.stat()
            except OSError:
                continue
            if (found.st_dev, found.st_ino) == (info.st_dev, info.st_ino):
                return path
        return None

    return other_name


def album_index(runtime: Runtime) -> Lookup:
    """Where the index of the analysed folders is.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The lookup to open with `index_of`.
    """
    return Lookup(runtime.locations.index_file, runtime.mapper)
