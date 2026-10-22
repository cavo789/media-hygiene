"""The files of an album of `albums.json`, where they are now (0298).

One notion of album: the named list the pages fill (search, browse, the burst review).
`album <name>` makes its folder of hard links on the disk, one more use of it next to
the TV, the phone and *Prepare for sending*. Each entry is followed if it moved
(`share.album_follow`); one not found, or of another size than when it was added, is
listed as missing: never linked on a guess.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.album_plan import Pick
from media_hygiene.errors import AlbumError
from media_hygiene.i18n import _
from media_hygiene.services.albums import album_store

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.albums import Album


@dataclass(frozen=True, slots=True)
class AlbumFiles:
    """An album of `albums.json`: its name as saved, its files found, those missing."""

    name: str
    picks: tuple[Pick, ...]
    missing: tuple[Path, ...]  # container paths


def album_files(runtime: Runtime, name: str) -> AlbumFiles:
    """Read an album of `albums.json` and find each of its files on the disk.

    Args:
        runtime: Settings, mount points and output.
        name: The album's name, whatever its case.

    Returns:
        Its files, in the album's order.

    Raises:
        AlbumError: No album of that name, or its file cannot be read or saved.
    """
    try:
        shelf = album_store(runtime).on_disk()
    except OSError as exc:  # a moved file found again, but /reports not writable
        raise AlbumError(
            _("Cannot read the albums file: {reason}").format(reason=exc),
            _("Mount the reports folder without ':ro'."),
        ) from exc
    album = shelf.albums.named(name)
    if album is None:
        names = ", ".join(each.name for each in shelf.albums.albums) or "-"
        raise AlbumError(
            _("No album named {name}. The albums: {names}.").format(
                name=name.strip(), names=names
            ),
            _(
                "Add photos to it in search or browse, or say what the album gathers "
                "from the classify plan: --category, --event, --rule or --rating."
            ),
        )
    return _found(runtime, album, frozenset(shelf.missing.get(album.name, ())))


def _found(runtime: Runtime, album: Album, gone: frozenset[str]) -> AlbumFiles:
    """Stat each entry where it is now; keep each file once.

    Args:
        runtime: Settings, mount points and output.
        album: The album, its moved entries followed.
        gone: The host paths of the entries not found again.

    Returns:
        Its files.
    """
    picks: list[Pick] = []
    missing: list[Path] = []
    seen: set[Path] = set()
    for entry in album.entries:
        path = runtime.mapper.to_container(entry.path)
        if path in seen:
            continue
        seen.add(path)
        try:
            info = path.stat()
        except OSError:
            missing.append(path)
            continue
        if entry.path in gone or not path.is_file() or info.st_size != entry.size:
            missing.append(path)
            continue
        picks.append(Pick(path, info.st_size, info.st_mtime_ns))
    return AlbumFiles(album.name, tuple(picks), tuple(missing))
