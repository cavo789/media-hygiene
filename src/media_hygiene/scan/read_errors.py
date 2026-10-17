"""Tell a read the disk or the cloud failed from a file that cannot be decoded.

A **read error** comes from outside the file: a disk with a bad moment, a USB disk
unplugged during the audit, a network drive, a OneDrive placeholder whose download
fails. It is an `OSError` carrying an `errno`. A **decoding failure** is everything
else: Pillow's own `OSError` without `errno` ("image file is truncated"),
`SyntaxError`, LibRaw's errors… Only a decoding failure makes a file broken: a file
that could not be read is listed, never stored, and read again at the next audit.
"""

from __future__ import annotations

import errno
import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from media_hygiene.scan.models import MediaFile

# The errors of a read a tool such as `ffprobe` reports by their system message.
READ_ERRNOS: Final = frozenset(
    {
        errno.EIO,
        errno.ETIMEDOUT,
        errno.EAGAIN,
        errno.ENXIO,
        errno.EACCES,
        errno.EPERM,
        errno.ENOENT,
        errno.ENODEV,
        errno.ESTALE,
        errno.EBUSY,
        errno.ENOTCONN,
        errno.ECONNRESET,
        errno.ECONNABORTED,
        errno.EHOSTDOWN,
        errno.EHOSTUNREACH,
        errno.ENETDOWN,
        errno.ENETUNREACH,
    }
)
_MESSAGES: Final = tuple(sorted(os.strerror(code) for code in READ_ERRNOS))
# How Python writes an `OSError` with an errno: what an older version stored.
_PYTHON_ERRNO: Final = re.compile(r"\[Errno \d+\]")


@dataclass(frozen=True, slots=True)
class UnreadFile:
    """A file the disk or the cloud could not read this time, and why."""

    file: MediaFile
    detail: str = ""


class ReadFailedError(Exception):
    """Raised by a check whose file could not be read: nothing is to be stored."""

    @property
    def detail(self) -> str:
        """The error, as the decoder or the tool told it.

        Returns:
            Its text.
        """
        return str(self.args[0]) if self.args else ""


def is_read_error(exc: BaseException) -> bool:
    """Tell whether a decoder's error is a failed read rather than a damaged file.

    Args:
        exc: The error raised while opening or decoding the file.

    Returns:
        True for an `OSError` that carries an `errno`.
    """
    return isinstance(exc, OSError) and exc.errno is not None


def is_read_error_message(line: str) -> bool:
    """Tell whether a tool's last error line is the system message of a failed read.

    `ffprobe` ends with `<path>: Input/output error` when the disk fails.

    Args:
        line: The tool's last line of error output.

    Returns:
        True when it ends with the message of a read error.
    """
    text = line.strip()
    return any(text.endswith(message) for message in _MESSAGES)


def is_stored_read_error(detail: str) -> bool:
    """Tell whether a verdict an older version stored was a failed read.

    Older versions stored every failure as "broken": those verdicts are checked again
    once.

    Args:
        detail: The stored detail of a broken file.

    Returns:
        True for an `OSError` with an errno, or a tool's read error message.
    """
    return bool(_PYTHON_ERRNO.search(detail)) or is_read_error_message(detail)
