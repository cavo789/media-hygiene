"""Read raw EXIF values safely: text padded with NULs, Pillow's rationals, tuples."""

from __future__ import annotations

import math
from typing import SupportsFloat


def text(value: object) -> str | None:
    """Clean an EXIF text value (bytes or str, padded with NULs or spaces).

    Args:
        value: The raw value.

    Returns:
        The text, or None when empty.
    """
    if isinstance(value, bytes):
        value = value.decode(errors="replace")
    if not isinstance(value, str):
        return None
    return value.strip("\x00 ").strip() or None


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
