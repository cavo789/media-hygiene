"""Move and copy user files without ever replacing an existing one.

A check (`exists()`) followed by an act (`rename`) leaves a gap: a file created in
between would be silently replaced by a POSIX rename, or truncated by a copy. Here the
refusal is the act itself:

- on one disk, `renameat2(RENAME_NOREPLACE)` renames atomically, or fails with EEXIST;
- where the kernel or the filesystem cannot do that (some FUSE, 9p or virtiofs
  mounts of Docker Desktop), and across disks, the target is created with
  `O_CREAT | O_EXCL`, filled, synced, proven identical to the source by its SHA-256,
  and only then is the source removed. A copy that differs is removed (it was created
  here), the source stays.
"""

from __future__ import annotations

import ctypes
import errno
import os
import shutil
from functools import cache
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

_AT_FDCWD: Final = -100
_RENAME_NOREPLACE: Final = 1
# The atomic rename is unavailable here, or cannot cross disks: copy instead.
COPY_INSTEAD: Final = frozenset(
    {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV}
)
_EXCLUSIVE_WRITE: Final = "xb"

type Renamer = Callable[[Path, Path], None]


@cache
def _libc_renameat2() -> Callable[..., int] | None:
    """Find `renameat2` in the C library (glibc 2.28 and later).

    Returns:
        The function, or None when the C library has none.
    """
    try:
        libc = ctypes.CDLL(None, use_errno=True)
    except OSError:  # pragma: no cover - every Linux has a C library
        return None
    function: Callable[..., int] | None = getattr(libc, "renameat2", None)
    return function


def rename_no_replace(source: Path, target: Path) -> None:
    """Rename `source` to `target` atomically, refusing an existing target.

    Args:
        source: The file.
        target: Its new name, on the same disk.

    Raises:
        OSError: EEXIST when the target exists, ENOSYS when the system cannot do it,
            EXDEV across disks, or any other error of the rename.
    """
    function = _libc_renameat2()
    if function is None:
        raise OSError(errno.ENOSYS, os.strerror(errno.ENOSYS), str(source))
    result = function(
        _AT_FDCWD,
        os.fsencode(source),
        _AT_FDCWD,
        os.fsencode(target),
        _RENAME_NOREPLACE,
    )
    if result != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(target))


def copy_exclusive(source: Path, target: Path) -> None:
    """Copy `source` to a new file `target`, never replacing one.

    Args:
        source: The file to copy.
        target: The copy; it must not exist.

    Raises:
        FileExistsError: The target exists (nothing was written).
        BaseException: The copy failed or was interrupted (the partial copy,
            created here, is removed first).
    """
    written = target.open(_EXCLUSIVE_WRITE)  # refused here: nothing was written
    try:
        with written, source.open("rb") as read:
            shutil.copyfileobj(read, written)
            written.flush()
            os.fsync(written.fileno())
        shutil.copystat(source, target)
    except BaseException:
        target.unlink()  # the partial copy, created here, never stays
        raise


def copy_then_remove(source: Path, target: Path) -> None:
    """Move a file by an exclusive copy, proven identical before the source goes.

    Args:
        source: The file to move.
        target: Where it goes; it must not exist.

    Raises:
        FileExistsError: The target exists (nothing changed).
        OSError: The copy differs from the original (the copy is removed, the
            original is kept).
    """
    copy_exclusive(source, target)
    if full_digest(source) != full_digest(target):
        target.unlink()
        raise OSError(_("the copy differs from the original"))
    source.unlink()


def move_no_replace(
    source: Path, target: Path, rename: Renamer = rename_no_replace
) -> None:
    """Move a file, never replacing anything: renamed on one disk, copied otherwise.

    Args:
        source: The file to move.
        target: Where it goes.
        rename: The atomic rename (replaceable in tests).

    Raises:
        FileExistsError: The target exists (nothing changed).
        OSError: The move failed; the source is still there.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        rename(source, target)
    except OSError as exc:
        if exc.errno not in COPY_INSTEAD:
            raise
        copy_then_remove(source, target)


def create_empty(path: Path) -> None:
    """Create an empty file, refusing an existing one.

    Args:
        path: The file.

    Raises:
        FileExistsError: It exists.
    """
    with path.open(_EXCLUSIVE_WRITE):
        pass
