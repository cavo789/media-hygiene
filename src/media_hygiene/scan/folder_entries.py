"""Sort the entries of one folder: media files, sidecars, the subfolders to visit.

The entries come from `os.scandir`, or from the index when the folder did not change
(`scan.folder_cache`): both read alike.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.scan.intruders import Intruder
from media_hygiene.scan.models import FileIdentity, MediaFile
from media_hygiene.scan.sidecars import Sidecar, companions_of, is_sidecar_of

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.scan.entry_like import EntryLike
    from media_hygiene.scan.filters import ScanFilters

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Listing:
    """What one folder holds: media files, sidecars, subfolders to visit, intruders."""

    files: tuple[MediaFile, ...] = ()
    folders: tuple[Path, ...] = ()
    sidecars: tuple[Sidecar, ...] = ()
    unreadable: tuple[Path, ...] = ()
    intruders: tuple[Intruder, ...] = ()


def sort_entries(items: Sequence[EntryLike], filters: ScanFilters) -> Listing:
    """Sort the entries of a folder: media files, sidecars, subfolders to visit.

    Args:
        items: Every entry of the folder.
        filters: Folders to skip and extensions to keep.

    Returns:
        What the folder holds, and the files that could not be `stat`ed.
    """
    described: list[MediaFile | Intruder | None] = []
    folders: list[Path] = []
    sidecars: list[EntryLike] = []
    unreadable: list[Path] = []
    names = tuple(item.name for item in items if not item.is_dir(follow_symlinks=False))
    for entry in items:
        path = Path(entry.path)
        if entry.is_dir(follow_symlinks=False):
            if not filters.skips_dir(path):
                folders.append(path)
            continue
        if is_sidecar_of(entry.name, names):
            sidecars.append(entry)
            continue
        try:
            described.append(_file(entry, path, filters))
        except OSError as exc:
            _LOGGER.warning("Cannot read %s: %s", path, exc.strerror)
            unreadable.append(path)
    return Listing(
        files=tuple(item for item in described if isinstance(item, MediaFile)),
        folders=tuple(folders),
        sidecars=_sidecars(sidecars, names),
        unreadable=tuple(unreadable),
        intruders=tuple(item for item in described if isinstance(item, Intruder)),
    )


def _file(
    entry: EntryLike, path: Path, filters: ScanFilters
) -> MediaFile | Intruder | None:
    """Describe a file that is not a sidecar: a media file kept, or an intruder.

    Args:
        entry: Its directory entry.
        path: Its path.
        filters: The extensions kept, the companions.

    Returns:
        The media file, the intruder, or None (a link, a media left out by `--ext`,
        a companion).

    Raises:
        OSError: The file cannot be `stat`ed.
    """
    if not filters.is_intruder(path):
        return _describe(entry, filters.kind_of(path))
    # An intruder is described like a sidecar: only its size and date matter.
    file = _describe(entry, MediaKind.SIDECAR)
    return None if file is None else Intruder(file.path, file.size, file.mtime_ns)


def _sidecars(
    entries: Sequence[EntryLike], names: tuple[str, ...]
) -> tuple[Sidecar, ...]:
    """Describe the sidecars of a folder, with the files each one belongs to.

    Args:
        entries: The sidecar entries of the folder.
        names: Names of every entry of the folder but its subfolders.

    Returns:
        The sidecars that are regular files.
    """
    found: list[Sidecar] = []
    for entry in entries:
        try:
            file = _describe(entry, MediaKind.SIDECAR)
        except OSError as exc:
            _LOGGER.warning("Cannot read %s: %s", entry.path, exc.strerror)
            continue
        if file is not None:
            found.append(Sidecar(file, companions_of(file.path, names)))
    return tuple(found)


def _describe(entry: EntryLike, kind: MediaKind | None) -> MediaFile | None:
    """Describe a directory entry when it is a regular file the walk keeps.

    Args:
        entry: The directory entry (its stat is cached by `scandir`, or the index).
        kind: What the file is, or None when the walk does not keep it.

    Returns:
        The file, or None for anything else (a link, a device, another extension).

    Raises:
        OSError: The file cannot be `stat`ed.
    """
    if kind is None or not entry.is_file(follow_symlinks=False):
        return None
    stat = entry.stat(follow_symlinks=False)
    return MediaFile(
        path=Path(entry.path),
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
        kind=kind,
        identity=FileIdentity(stat.st_dev, stat.st_ino) if stat.st_ino else None,
    )
