"""The pairing of a phone with the run's code, and the page that asks for it (0269).

Wrong codes are counted per device address (`lan_attempts`, 0681).
Shared by the home page's door (`lan_app`) and the slideshow's (`slideshow/door`).
"""

from __future__ import annotations

import time
from dataclasses import replace
from functools import cache
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _, active_locale
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.lan import CODE_DIGITS, COOKIE_NAME, PAIR_PREFIX
from media_hygiene.review.lan_attempts import Attempts
from media_hygiene.review.lan_phones import device_name
from media_hygiene.review.local_app import PAGE_PATH

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.review.lan import LanAccess

_PACKAGE: Final = "media_hygiene.review"
_PAIR_TEMPLATE: Final = "lan_pair.html.j2"
_MAX_PAIRED: Final = 20  # new devices of the run listed on the PC's card


class Pairing:
    """The run's pairing: wrong codes by address, the code's version, new devices."""

    __slots__ = ("attempts", "generation", "paired")

    def __init__(self) -> None:
        """Start without any wrong code, on the code `mh --lan` derived first."""
        self.attempts = Attempts()
        self.generation = 0
        self.paired: list[dict[str, object]] = []

    @property
    def closed(self) -> bool:
        """Tell whether the run's ceiling of wrong codes is reached.

        Returns:
            True from `MAX_FAILURES` on, until the PC opens the pairing again.
        """
        return self.attempts.closed

    def access(self, lan: LanAccess) -> LanAccess:
        """The run's access with the code of the current generation.

        Args:
            lan: The access `mh --lan` gave.

        Returns:
            The same, its code the one the PC's card shows now.
        """
        return replace(lan, generation=self.generation)

    def reopen(self) -> None:
        """Open the pairing again with a new code: the old one opens nothing now."""
        self.generation += 1
        self.attempts.reopen()

    def check(self, lan: LanAccess, request: Request) -> Response:
        """Check a code; the right one sets the phone's cookie and opens `/`.

        Args:
            lan: The run's access.
            request: `GET /pair/<code>`, from the device's address (`peer`).

        Returns:
            303 to `/` with the cookie; the pairing page again otherwise: 429 while
            this address waits or once the run's ceiling is reached.
        """
        if self.closed:
            return pair_page(HTTPStatus.TOO_MANY_REQUESTS, closed=True)
        if self.attempts.waiting(request.peer):
            return pair_page(HTTPStatus.TOO_MANY_REQUESTS, closed=False)
        typed = request.path.removeprefix(PAIR_PREFIX)
        if not self.access(lan).code_matches(typed):
            self.attempts.failed(request.peer)
            return pair_page(HTTPStatus.FORBIDDEN, closed=self.closed)
        name = device_name(request.headers.get("user-agent", ""))
        self.paired = [*self.paired, {"name": name, "at": int(time.time() * 1000)}]
        self.paired = self.paired[-_MAX_PAIRED:]
        secure = "; Secure" if lan.secure else ""  # HTTPS (0430)
        cookie = f"{COOKIE_NAME}={lan.token}; Path=/; HttpOnly; SameSite=Lax{secure}"
        headers = (f"Location: {PAGE_PATH}", f"Set-Cookie: {cookie}")
        return Response(HTTPStatus.SEE_OTHER, headers=headers)


def pair_page(status: HTTPStatus, *, closed: bool) -> Response:
    """The pairing page, and why the last code was refused.

    Args:
        status: 401 before any code, 403 after a wrong one, 429 while this
            device waits, or once closed.
        closed: Too many wrong codes: no form any more.

    Returns:
        The page.
    """
    problem = ""
    if closed:
        problem = _(
            "Too many wrong codes: pairing is closed. On the PC, choose Open pairing "
            "again on the home page for a new code."
        )
    elif status is HTTPStatus.TOO_MANY_REQUESTS:
        problem = _(
            "Too many wrong codes from this device: wait a minute, then type the code "
            "shown on the PC."
        )
    elif status is HTTPStatus.FORBIDDEN:
        problem = _("This is not the code shown on the PC: type it again.")
    return Response(
        status, _drawn(problem, closed, str(active_locale())), ContentType.HTML
    )


@cache
def _drawn(problem: str, closed: bool, locale: str) -> bytes:  # noqa: FBT001
    """The pairing page, drawn once per text and language: never the disk again (0682).

    Args:
        problem: Why the last code was refused; empty before any code.
        closed: Too many wrong codes: no form any more.
        locale: The language in use (its texts are drawn in it).

    Returns:
        The page.
    """
    del locale  # in the key only: the template's texts follow the language in use
    template = translated_environment(_PACKAGE, escaped=("html", "j2")).get_template(
        _PAIR_TEMPLATE
    )
    page = template.render(
        problem=problem, closed=closed, digits=CODE_DIGITS, prefix=PAIR_PREFIX
    )
    return page.encode()
