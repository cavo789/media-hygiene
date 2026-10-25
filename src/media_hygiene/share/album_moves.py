"""`albums.json` follows the files `sort` or `undo` moved, right away (0382).

`album_follow` finds a moved file again when an album is read, through the index: a
cache. Rewritten by the run that moved the files, the albums no longer depend on it.
The moves are known, so no file is read: each entry moved takes its new host path,
its digest and size kept. Saved at once, then read back from the disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.share.albums import read_albums, write_albums

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


def follow_albums(path: Path, moves: Mapping[str, str]) -> int:
    """Give each album entry whose file moved its new path.

    Args:
        path: `albums.json`, in the container; missing: nothing to do.
        moves: New host path by old one.

    Returns:
        The entries renamed, counted on the file read back.

    Raises:
        AlbumsError: The file is not an albums file.
        OSError: It cannot be written.
    """
    if not path.is_file():
        return 0
    before = read_albums(path)
    albums = tuple(
        album.model_copy(
            update={
                "entries": tuple(
                    entry.model_copy(update={"path": moves.get(entry.path, entry.path)})
                    for entry in album.entries
                )
            }
        )
        for album in before.albums
    )
    after = before.model_copy(update={"albums": albums})
    if after == before:
        return 0
    write_albums(path, after)
    targets = set(moves.values())
    back = read_albums(path)
    return sum(1 for a in back.albums for entry in a.entries if entry.path in targets)
