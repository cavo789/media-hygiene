"""Read raw EXIF values safely: text padded with NULs, Pillow's rationals, tuples."""

from __future__ import annotations

import math
import re
from typing import Final, SupportsFloat

# C0 control characters but tab, line feed and carriage return: junk in EXIF text.
_CONTROL: Final = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def text(value: object) -> str | None:
    """Clean an EXIF text value (bytes or str, padded or filled with NULs, spaces).

    Args:
        value: The raw value.

    Returns:
        The text, or None when empty.
    """
    if isinstance(value, bytes):
        value = value.decode(errors="replace")
    if not isinstance(value, str):
        return None
    # EXIF text ends at its first NUL: what follows is leftover bytes.
    value = value.strip("\x00 ").partition("\x00")[0]
    return _CONTROL.sub("", value).strip() or None


def number(value: object) -> float | None:
    """Read an EXIF number (Pillow's rationals included).

    Args:
        value: The raw value.

    Returns:
        The number, or None when it is not a finite one (a zero denominator, text).
    """
    if not isinstance(value, SupportsFloat) or isinstance(value, str):
        return None
    try:
        result = float(value)
    except ValueError, ZeroDivisionError, OverflowError:
        return None
    return result if math.isfinite(result) else None


def integer(value: object) -> int | None:
    """Read an EXIF integer, the first one of a tuple (ISO is sometimes one).

    Args:
        value: The raw value.

    Returns:
        The integer, or None when it is not one.
    """
    if isinstance(value, tuple | list):
        value = value[0] if value else None
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
