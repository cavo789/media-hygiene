"""Read and parse a settings file once while it stays the same on disk (2026-11-15).

`/config` is a Windows folder mounted into the container: each open and read there
costs milliseconds, and a naming on the people pages read every person's file four
times (measured on the maintainer's PC: 0.8 s per full read, 4 s per name, growing
with each person named). The text is kept by the file's stamp — inode, size,
modification and change times in nanoseconds, as `people_memo` — so one `stat`
tells it is still the same: an edit by hand, an atomic save (new inode), an
in-place write, a copy keeping the modification time or a `touch` each change the
stamp and the file is read again. `stamped_value` keeps what a parser made of the
text too: parsing every person's file was the larger part (1.3 MB of faces: 0.2 s
per read here, 0.8 s on the maintainer's PC, and the fan on). What it returns is
shared: callers read it, never change it.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Final, cast

if TYPE_CHECKING:
    from collections.abc import Callable
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
    return _read(path, _stamp(path))


def stamped_value[T](path: Path, parse: Callable[[str], T]) -> T:
    """What `parse` makes of a file's text, made again only when its stamp changed.

    Args:
        path: The file.
        parse: A module-level function (it is part of the key), e.g. `tomllib.loads`.

    Returns:
        Its result, shared between callers: never change it.

    Raises:
        OSError: The file cannot be read (missing included).
        UnicodeDecodeError: It is not UTF-8.
    """
    stamp = _stamp(path)
    return cast("T", _parsed(path, stamp, parse))


def _stamp(path: Path) -> Stamp:
    """A file's inode, size, modification and change times.

    Args:
        path: The file.

    Returns:
        Its stamp.
    """
    status = path.stat()
    return (status.st_ino, status.st_size, status.st_mtime_ns, status.st_ctime_ns)


@functools.lru_cache(maxsize=_KEPT_FILES)
def _parsed(path: Path, stamp: Stamp, parse: Callable[[str], object]) -> object:
    """Parse a file's text; cached by path, stamp and parser.

    Args:
        path: The file.
        stamp: Its stamp.
        parse: The parser.

    Returns:
        What it made.
    """
    return parse(_read(path, stamp))


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
    _parsed.cache_clear()
