r"""What the PC holds of a phone file's content: library, import, journals (0248).

Each check reads the PC's files only, never the phone's: the staged copy's SHA-256
is computed once by `phone_proof`, then compared here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.hashing import full_digest, partial_digest

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.returned import Remembered, RememberedSet

_PARENT: Final = ".."


@dataclass(frozen=True, slots=True)
class LibraryRow:
    """A file of the index: where, when it was digested, its SHA-256 if known."""

    path: Path  # in the container
    mtime_ns: int
    full: str | None


@dataclass(frozen=True, slots=True)
class Holdings:
    """What the PC holds, gathered once for every file ticked."""

    mapper: HostPathMapper
    library: Mapping[int, tuple[LibraryRow, ...]]  # by size, in path order
    remembered: RememberedSet
    quarantined: frozenset[str]  # the runs whose quarantine is still there
    destination: Path | None = None  # the import's folder, in the container


def in_library(rows: tuple[LibraryRow, ...], size: int, digest: str) -> Path | None:
    """Find a file of the library holding that content, there now.

    Args:
        rows: The files of the index of that size, in path order.
        size: The size of the phone file.
        digest: Its SHA-256.

    Returns:
        The first file found, in the container; None when none holds it now.
    """
    return next((row.path for row in rows if _holds(row, size, digest)), None)


def _holds(row: LibraryRow, size: int, digest: str) -> bool:
    """Tell whether a file of the index holds that content now.

    The index's digest is trusted while the file's size and date are unchanged;
    otherwise, or without one, the file is read now.

    Args:
        row: The file, as the index knows it.
        size: The size of the phone file.
        digest: Its SHA-256.

    Returns:
        True when it is there, of that size and content; False when gone.
    """
    try:
        stat = row.path.stat()
        if stat.st_size != size:
            return False
        if row.full is not None and stat.st_mtime_ns == row.mtime_ns:
            return row.full == digest
        return full_digest(row.path) == digest
    except OSError:
        return False


def imported_copy(
    destination: Path, relative: str, key: tuple[int, str]
) -> Path | None:
    """Find the import's copy of a phone file, whole and of the same content.

    Args:
        destination: The import's folder, in the container.
        relative: The copy's path in it, as the plan names it.
        key: The phone file's size and the SHA-256 of its staged copy.

    Returns:
        The copy, or None; a path leaving the folder is never followed.
    """
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or _PARENT in path.parts:
        return None
    copy = destination.joinpath(*path.parts)
    size, digest = key
    try:
        same = copy.stat().st_size == size and full_digest(copy) == digest
    except OSError:
        return None
    return copy if same else None


def remembered_content(
    staged: Path, key: tuple[int, str], remembered: RememberedSet
) -> Remembered | None:
    """Find the content in the journals: its SHA-256, else its partial digest.

    Args:
        staged: The staged copy.
        key: Its size and SHA-256.
        remembered: What the journals remember.

    Returns:
        The set-aside, or None.
    """
    if (said := remembered.by_digest.get(key)) is not None:
        return said
    if not remembered.by_partial:
        return None
    try:
        partial = partial_digest(staged)
    except OSError:
        return None
    return remembered.by_partial.get((key[0], partial))
