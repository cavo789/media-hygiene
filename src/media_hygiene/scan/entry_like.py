"""What the walk reads of a folder entry: an `os.DirEntry`, or one the index kept."""

from __future__ import annotations

from typing import Protocol


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
