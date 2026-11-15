"""Read a settings file once while it stays the same on disk (2026-11-15).

`/config` is a Windows folder mounted into the container: each open and read there
costs milliseconds, and a naming on the people pages read every person's file four
times (measured on the maintainer's PC: 0.8 s per full read, 4 s per name, growing
with each person named). The text is kept by the file's stamp — inode, size,
modification and change times in nanoseconds, as `people_memo` — so one `stat`
tells it is still the same: an edit by hand, an atomic save (new inode), an
in-place write, a copy keeping the modification time or a `touch` each change the
stamp and the file is read again.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

ENCODING: Final = "utf-8"
# Files kept: a person's file each, plus `config.toml` and the ignored faces.
_KEPT_FILES: Final = 4096

type Stamp = tuple[int, int, int, int]


def stamped_text(path: Path) -> str:
    """The text of a file, read again only when its stamp changed.

    Args:
        path: The file.

    Returns:
        Its text, decoded as UTF-8.

    Raises:
        OSError: The file cannot be read (missing included).
        UnicodeDecodeError: It is not UTF-8.
    """
    status = path.stat()
    stamp = (status.st_ino, status.st_size, status.st_mtime_ns, status.st_ctime_ns)
    return _read(path, stamp)


@functools.lru_cache(maxsize=_KEPT_FILES)
def _read(path: Path, stamp: Stamp) -> str:  # noqa: ARG001  # pylint: disable=unused-argument
    """Read a file; cached by path and stamp (the stamp is only the key).

    Args:
        path: The file.
        stamp: Its inode, size, modification and change times.

    Returns:
        Its text.
    """
    return path.read_text(ENCODING)


def forget_texts() -> None:
    """Drop every text kept (tests start cold)."""
    _read.cache_clear()
