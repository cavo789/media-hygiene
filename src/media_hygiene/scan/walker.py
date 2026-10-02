"""List every media file and sidecar below the data roots, without following links.

Folders are read concurrently: on a Windows drive seen through Docker, each directory
listing waits for a slow round trip, so several are kept in flight at once.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.constants import ALBUM_MARKER, MediaKind, Sizes
from media_hygiene.scan.models import FileIdentity, MediaFile
from media_hygiene.scan.sidecars import Sidecar, companions_of, is_sidecar

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.scan.filters import ScanFilters
    from media_hygiene.scan.progress import ProgressSink

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Walk:
    """What the walk found below the roots, in no fixed order.

    `unreadable` lists the folders it could not read and the files it could not
    `stat`: whatever lies there may exist, the walk just could not see it.
    """

    files: tuple[MediaFile, ...] = ()
    sidecars: tuple[Sidecar, ...] = ()
    unreadable: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class _Listing:
    """What one folder holds: its media files, its sidecars, the subfolders to visit."""

    files: tuple[MediaFile, ...] = ()
    folders: tuple[Path, ...] = ()
    sidecars: tuple[Sidecar, ...] = ()
    unreadable: tuple[Path, ...] = ()


async def walk(
    roots: Iterable[Path],
    filters: ScanFilters,
    progress: ProgressSink,
) -> Walk:
    """Return the media files and sidecars below `roots`, as `filters` allows.

    Unreadable folders and files are logged, skipped and listed: one bad folder
    never stops the scan.
    Nested or overlapping roots list their files twice: see `unique_files`.
    Sidecars are listed whatever the extension filter: they follow their photo.

    Args:
        roots: Folders to walk.
        filters: Folders to skip and extensions to keep.
        progress: Advanced once per media file found.

    Returns:
        Every media file and sidecar found, and what could not be read.
    """
    files: list[MediaFile] = []
    sidecars: list[Sidecar] = []
    unreadable: list[Path] = []
    visits: list[asyncio.Task[None]] = []
    slots = asyncio.Semaphore(Sizes.IO_CONCURRENCY)
    async with asyncio.TaskGroup() as group:

        async def visit(folder: Path) -> None:
            async with slots:
                listing = await asyncio.to_thread(_list_folder, folder, filters)
            files.extend(listing.files)
            sidecars.extend(listing.sidecars)
            unreadable.extend(listing.unreadable)
            for _file in listing.files:
                progress.advance()
            visits.extend(group.create_task(visit(sub)) for sub in listing.folders)

        visits.extend(group.create_task(visit(root)) for root in roots)
    return Walk(tuple(files), tuple(sidecars), tuple(unreadable))


def _list_folder(folder: Path, filters: ScanFilters) -> _Listing:
    """Read one folder (runs in a worker thread).

    Args:
        folder: Folder to read.
        filters: Folders to skip and extensions to keep.

    Returns:
        Its media files, sidecars and the subfolders to visit; nothing when it cannot
        be read, or is an album.
    """
    try:
        with os.scandir(folder) as entries:
            items = list(entries)
    except OSError as exc:
        _LOGGER.warning("Cannot read folder %s: %s", folder, exc.strerror)
        return _Listing(unreadable=(folder,))
    if any(item.name == ALBUM_MARKER for item in items):
        return _Listing()  # an album: second names of files listed where they are
    return _sort_entries(items, filters)


def _sort_entries(items: list[os.DirEntry[str]], filters: ScanFilters) -> _Listing:
    """Sort the entries of a folder: media files, sidecars, subfolders to visit.

    Args:
        items: Every entry of the folder.
        filters: Folders to skip and extensions to keep.

    Returns:
        What the folder holds, and the files that could not be `stat`ed.
    """
    files: list[MediaFile] = []
    folders: list[Path] = []
    sidecars: list[os.DirEntry[str]] = []
    unreadable: list[Path] = []
    for entry in items:
        path = Path(entry.path)
        if entry.is_dir(follow_symlinks=False):
            if not filters.skips_dir(path):
                folders.append(path)
            continue
        if is_sidecar(entry.name):
            sidecars.append(entry)
            continue
        try:
            media = _describe(entry, filters.kind_of(path))
        except OSError as exc:
            _LOGGER.warning("Cannot read %s: %s", path, exc.strerror)
            unreadable.append(path)
            continue
        if media is not None:
            files.append(media)
    return _Listing(
        tuple(files), tuple(folders), _sidecars(sidecars, items), tuple(unreadable)
    )


def _sidecars(
    entries: list[os.DirEntry[str]], items: list[os.DirEntry[str]]
) -> tuple[Sidecar, ...]:
    """Describe the sidecars of a folder, with the files each one belongs to.

    Args:
        entries: The sidecar entries of the folder.
        items: Every entry of the folder.

    Returns:
        The sidecars that are regular files.
    """
    if not entries:
        return ()
    names = [item.name for item in items if not item.is_dir(follow_symlinks=False)]
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


def _describe(entry: os.DirEntry[str], kind: MediaKind | None) -> MediaFile | None:
    """Describe a directory entry when it is a regular file the walk keeps.

    Args:
        entry: The directory entry (its stat is cached by `scandir`).
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
