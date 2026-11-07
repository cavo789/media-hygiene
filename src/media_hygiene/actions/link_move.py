"""Move a file by a hard link then the removal of its old name: instant, no copy.

Docker Desktop's NTFS mounts refuse `renameat2(RENAME_NOREPLACE)` but make true hard
links. `link()` refuses an existing target like that rename does: the refusal is the
act itself, so nothing is ever replaced.
"""

from __future__ import annotations

import errno
import os
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

# A hard link cannot be made either (another disk, a filesystem without links).
_NO_LINK: Final = frozenset(
    {errno.EXDEV, errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS}
)


def moved_by_link(source: Path, target: Path) -> bool:
    """Move a file by a second name, then the removal of the first one.

    Args:
        source: The file to move.
        target: Where it goes; it must not exist.

    Returns:
        False when hard links cannot be made here: nothing changed.

    Raises:
        FileExistsError: The target exists (nothing changed).
        OSError: Any other error of the link; nothing changed.
    """
    try:
        os.link(source, target)
    except OSError as exc:
        if exc.errno in _NO_LINK:
            return False
        raise
    source.unlink()
    return True


def same_file(source: Path, target: Path) -> bool:
    """Tell whether two names hold the very same file (one inode).

    Args:
        source: A name.
        target: Another one.

    Returns:
        True when both exist and are the same file.
    """
    try:
        return source.samefile(target)
    except OSError:
        return False


def linked_move(source: Path, target: Path) -> bool:
    """Move a file by a hard link then the removal of its old name, where possible.

    Args:
        source: The file.
        target: Where it goes; never overwritten.

    Returns:
        False when no link can be made (another disk, a filesystem without links):
        nothing changed, the file is to be copied.

    Raises:
        FileExistsError: Something is at the target already (nothing changed).
    """
    try:
        return moved_by_link(source, target)
    except FileExistsError:
        raise target_exists(target) from None


def target_exists(target: Path) -> FileExistsError:
    """The refusal of a move whose target exists: nothing is replaced, nothing moves.

    Args:
        target: Where the file was to go.

    Returns:
        The error to raise.
    """
    return FileExistsError(errno.EEXIST, _("the target exists"), str(target))
