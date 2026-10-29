"""The TVs of the show, paired the other way round: a code on the TV, typed on a phone.

Typing with a TV remote is painful; reading a code on the TV is not. A TV opening the
screen page gets a token of its own in a cookie and a short code to show; a phone
already paired (`mh --lan`'s code) types that code on its remote, and from then on the
TV's token opens the show. Under HTTPS `mh --lan` a TV paired is kept for good (0456):
its token's hash in `/lan/tvs.json` (`PhoneBook`, the phones' rules), forgotten on the
PC's card; otherwise tokens live in memory and the next run pairs the TV again. At
most `MAX_WAITING` TVs wait at once (the oldest forgotten) and `MAX_FAILURES` wrong
codes close the pairing of TVs until the server stops.
"""

from __future__ import annotations

import hmac
import secrets
import time
from typing import TYPE_CHECKING, Final

from media_hygiene.review.lan_phones import TV_NAME
from media_hygiene.slideshow.chapters import Telling
from media_hygiene.slideshow.screen_codes import draw_code

if TYPE_CHECKING:
    from media_hygiene.review.lan_phones import PhoneBook

SCREEN_COOKIE: Final = "mh_screen"
MAX_WAITING: Final = 8
MAX_FAILURES: Final = 5
_TOKEN_BYTES: Final = 32
WAITING_SECONDS: Final = 60.0  # a TV asked its code this recently: field on top


class Screens:
    """The TVs waiting for their code to be typed, and those paired."""

    __slots__ = (
        "_asked",
        "_book",
        "_paired",
        "_photos_only",
        "_waiting",
        "failures",
        "telling",
    )

    def __init__(self, book: PhoneBook | None = None) -> None:
        """Start without any TV in memory.

        Args:
            book: `tvs.json` under HTTPS: the TVs paired for good; None in memory only.
        """
        self._book = book
        self._asked = -WAITING_SECONDS  # when a TV last asked for its code
        self._waiting: dict[str, str] = {}  # token -> code, oldest first
        self._paired: set[str] = set()
        self._photos_only: set[str] = set()  # TVs whose browser plays no video
        self.failures = 0
        self.telling = Telling.TV  # where the events are told, chosen on the phone

    @property
    def films(self) -> bool:
        """Tell whether the show's videos are shown: a TV paired plays them.

        Returns:
            False once every TV paired shows photos only; True without any TV.
        """
        return not self._paired or not self._paired <= self._photos_only

    def tell(self, token: str, *, films: bool) -> None:
        """Record whether a TV paired plays videos, as its page found out.

        Args:
            token: The TV's cookie.
            films: True when its browser plays them.
        """
        if token not in self._paired:
            return
        if films:
            self._photos_only.discard(token)
        else:
            self._photos_only.add(token)

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
            True for a TV paired by this server, or kept in `tvs.json`.
        """
        if any(
            hmac.compare_digest(token.encode(), known.encode())
            for known in self._paired
        ):
            return True
        if self._book is None or not self._book.knows(token):
            return False
        self._paired.add(token)  # paired before a restart: counted from now on
        return True

    @property
    def waiting(self) -> bool:
        """Tell whether a TV shows its code now, for a phone to type it.

        Returns:
            True when a TV not paired asked for its code in the last minute.
        """
        recent = time.monotonic() - self._asked < WAITING_SECONDS
        return bool(self._waiting) and recent

    def code_of(self, token: str) -> str | None:
        """The code a waiting TV shows.

        Args:
            token: The TV's cookie.

        Returns:
            The code, or None for a token not waiting.
        """
        code = self._waiting.get(token)
        if code is not None:
            self._asked = time.monotonic()
        return code

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
        code = draw_code()
        while code in taken:
            code = draw_code()
        self._waiting[fresh] = code
        self._asked = time.monotonic()
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
                if self._book is not None:
                    self._book.keep(token, TV_NAME)  # unwritten: in memory still
                return True
        self.failures += 1
        return False


def screens_of(phones: PhoneBook | None) -> Screens:
    """The TVs of a run: kept beside the phones paired for good (0456), else in memory.

    Args:
        phones: `phones.json` under HTTPS; None otherwise.

    Returns:
        The TVs, none paired in memory yet.
    """
    return Screens(None if phones is None else phones.tvs())
