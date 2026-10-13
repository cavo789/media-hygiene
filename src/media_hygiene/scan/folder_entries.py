"""Sort the entries of one folder: media files, sidecars, the subfolders to visit.

The entries come from `os.scandir`, or from the index when the folder did not change
(`scan.folder_cache`): both read alike.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from media_hygiene.constants import MediaKind
from media_hygiene.scan.models import FileIdentity, MediaFile
from media_hygiene.scan.sidecars import Sidecar, companions_of, is_sidecar

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.scan.filters import ScanFilters

_LOGGER = logging.getLogger(__name__)


class StatLike(Protocol):
    """The `stat` fields the walk reads."""

    @property
    def st_size(self) -> int:
        """Size in bytes."""

    @property
    def st_mtime_ns(self) -> int:
        """Modification time, in nanoseconds."""

    @property
    def st_dev(self) -> int:
        """Device of the file system."""

    @property
    def st_ino(self) -> int:
        """Inode: with the device, the file's identity."""


class EntryLike(Protocol):
    """A folder entry: an `os.DirEntry`, or one the index kept."""

    @property
    def path(self) -> str:
        """The entry's path."""

    @property
    def name(self) -> str:
        """The entry's name."""

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        """Tell whether it is a folder.

        Args:
            follow_symlinks: Whether to follow a link (the walk never does).

        Returns:
            True for a folder.
        """

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        """Tell whether it is a regular file.

        Args:
            follow_symlinks: Whether to follow a link (the walk never does).

        Returns:
            True for a regular file.
        """

    def stat(self, *, follow_symlinks: bool = True) -> StatLike:
        """Its size, time and identity.

        Args:
            follow_symlinks: Whether to follow a link (the walk never does).

        Returns:
            The `stat` fields.
        """


@dataclass(frozen=True, slots=True)
class Listing:
    """What one folder holds: its media files, its sidecars, the subfolders to visit."""

    files: tuple[MediaFile, ...] = ()
    folders: tuple[Path, ...] = ()
    sidecars: tuple[Sidecar, ...] = ()
    unreadable: tuple[Path, ...] = ()


def sort_entries(items: Sequence[EntryLike], filters: ScanFilters) -> Listing:
    """Sort the entries of a folder: media files, sidecars, subfolders to visit.

    Args:
        items: Every entry of the folder.
        filters: Folders to skip and extensions to keep.

    Returns:
        What the folder holds, and the files that could not be `stat`ed.
    """
    files: list[MediaFile] = []
    folders: list[Path] = []
    sidecars: list[EntryLike] = []
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
    return Listing(
        tuple(files), tuple(folders), _sidecars(sidecars, items), tuple(unreadable)
    )


def _sidecars(
    entries: Sequence[EntryLike], items: Sequence[EntryLike]
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
