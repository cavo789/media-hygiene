"""The TVs of the show, paired the other way round: a code on the TV, typed on a phone.

Typing with a TV remote is painful; reading a code on the TV is not. A TV opening the
screen page gets a token of its own in a cookie and a short code to show; a phone
already paired (`mh --lan`'s code) types that code on its remote, and from then on the
TV's token opens the show. Tokens and codes are drawn for this server only, never
written anywhere: the next `slideshow` pairs the TV again. At most `MAX_WAITING` TVs
wait at once (the oldest forgotten) and `MAX_FAILURES` wrong codes close the pairing
of TVs until the server stops.
"""

from __future__ import annotations

import hmac
import secrets
from typing import Final

SCREEN_COOKIE: Final = "mh_screen"
SCREEN_DIGITS: Final = 6  # read on the TV, typed on the phone
MAX_WAITING: Final = 8
MAX_FAILURES: Final = 5
_TOKEN_BYTES: Final = 32
_HALF: Final = SCREEN_DIGITS // 2


class Screens:
    """The TVs waiting for their code to be typed, and those paired."""

    __slots__ = ("_paired", "_waiting", "failures")

    def __init__(self) -> None:
        """Start without any TV."""
        self._waiting: dict[str, str] = {}  # token -> code, oldest first
        self._paired: set[str] = set()
        self.failures = 0

    @property
    def paired(self) -> int:
        """How many TVs were paired.

        Returns:
            Their number.
        """
        return len(self._paired)

    @property
    def closed(self) -> bool:
        """Tell whether too many wrong codes were typed.

        Returns:
            True from `MAX_FAILURES` on.
        """
        return self.failures >= MAX_FAILURES

    def is_paired(self, token: str) -> bool:
        """Tell whether a TV's token opens the show.

        Args:
            token: The TV's cookie, empty without one.

        Returns:
            True for a TV paired by this server.
        """
        return any(
            hmac.compare_digest(token.encode(), known.encode())
            for known in self._paired
        )

    def code_of(self, token: str) -> str | None:
        """The code a waiting TV shows.

        Args:
            token: The TV's cookie.

        Returns:
            The code, or None for a token not waiting.
        """
        return self._waiting.get(token)

    def arrive(self, token: str) -> str | None:
        """Give a TV opening the screen page a token, unless it holds a known one.

        Args:
            token: Its cookie, empty without one.

        Returns:
            A new token to set in its cookie; None when its own is still known.
        """
        if token in self._waiting or self.is_paired(token):
            return None
        while len(self._waiting) >= MAX_WAITING:
            del self._waiting[next(iter(self._waiting))]
        fresh = secrets.token_hex(_TOKEN_BYTES)
        taken = set(self._waiting.values())
        code = _draw_code()
        while code in taken:
            code = _draw_code()
        self._waiting[fresh] = code
        return fresh

    def confirm(self, typed: str) -> bool:
        """Pair the TV showing the code typed on the phone.

        Args:
            typed: The code, spaces ignored.

        Returns:
            True when a waiting TV showed it; a wrong code counts as a failure.
        """
        if self.closed:
            return False
        cleaned = "".join(char for char in typed if char.isdigit())
        for token, code in self._waiting.items():
            if hmac.compare_digest(cleaned.encode(), code.encode()):
                del self._waiting[token]
                self._paired.add(token)
                return True
        self.failures += 1
        return False


def shown_code(code: str) -> str:
    """The code as the TV shows it: two groups of three digits.

    Args:
        code: `SCREEN_DIGITS` digits.

    Returns:
        E.g. `123 456`.
    """
    return f"{code[:_HALF]} {code[_HALF:]}"


def _draw_code() -> str:
    """Draw a code.

    Returns:
        `SCREEN_DIGITS` digits.
    """
    return str(secrets.randbelow(10**SCREEN_DIGITS)).zfill(SCREEN_DIGITS)
