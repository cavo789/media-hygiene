"""The code a TV shows to be paired: drawn, then shown in two groups."""

from __future__ import annotations

import secrets
from typing import Final

SCREEN_DIGITS: Final = 6  # read on the TV, typed on the phone
_HALF: Final = SCREEN_DIGITS // 2


def shown_code(code: str) -> str:
    """The code as the TV shows it: two groups of three digits.

    Args:
        code: `SCREEN_DIGITS` digits.

    Returns:
        E.g. `123 456`.
    """
    return f"{code[:_HALF]} {code[_HALF:]}"


def draw_code() -> str:
    """Draw a code.

    Returns:
        `SCREEN_DIGITS` digits.
    """
    return str(secrets.randbelow(10**SCREEN_DIGITS)).zfill(SCREEN_DIGITS)
