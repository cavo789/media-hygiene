"""The pairing of a phone with the run's code, and the page that asks for it (0269).

Shared by the home page's door (`lan_app`) and the slideshow's (`slideshow/door`).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.lan import CODE_DIGITS, COOKIE_NAME, PAIR_PREFIX
from media_hygiene.review.local_app import PAGE_PATH

if TYPE_CHECKING:
    from media_hygiene.review.lan import LanAccess

MAX_FAILURES: Final = 5  # wrong codes before the pairing closes for this server
_PACKAGE: Final = "media_hygiene.review"
_PAIR_TEMPLATE: Final = "lan_pair.html.j2"


class Pairing:
    """The wrong codes typed so far, for this server."""

    __slots__ = ("failures",)

    def __init__(self) -> None:
        """Start without any wrong code."""
        self.failures = 0

    @property
    def closed(self) -> bool:
        """Tell whether too many wrong codes were typed.

        Returns:
            True from `MAX_FAILURES` on.
        """
        return self.failures >= MAX_FAILURES

    def check(self, lan: LanAccess, typed: str) -> Response:
        """Check a code; the right one sets the phone's cookie and opens `/`.

        Args:
            lan: The run's access.
            typed: The code, from the path.

        Returns:
            303 to `/` with the cookie; the pairing page again otherwise.
        """
        if self.closed:
            return pair_page(HTTPStatus.TOO_MANY_REQUESTS, closed=True)
        if not lan.code_matches(typed):
            self.failures += 1
            return pair_page(HTTPStatus.FORBIDDEN, closed=self.closed)
        secure = "; Secure" if lan.secure else ""  # HTTPS (0430)
        cookie = f"{COOKIE_NAME}={lan.token}; Path=/; HttpOnly; SameSite=Lax{secure}"
        headers = (f"Location: {PAGE_PATH}", f"Set-Cookie: {cookie}")
        return Response(HTTPStatus.SEE_OTHER, headers=headers)


def pair_page(status: HTTPStatus, *, closed: bool) -> Response:
    """The pairing page, and why the last code was refused.

    Args:
        status: 401 before any code, 403 after a wrong one, 429 once closed.
        closed: Too many wrong codes: no form any more.

    Returns:
        The page.
    """
    problem = ""
    if closed:
        problem = _(
            "Too many wrong codes: pairing is closed. On the PC, quit Media Hygiene, "
            "then type mh --lan again for a new code."
        )
    elif status is HTTPStatus.FORBIDDEN:
        problem = _("This is not the code shown on the PC: type it again.")
    template = translated_environment(_PACKAGE, escaped=("html", "j2")).get_template(
        _PAIR_TEMPLATE
    )
    page = template.render(
        problem=problem, closed=closed, digits=CODE_DIGITS, prefix=PAIR_PREFIX
    )
    return Response(status, page.encode(), ContentType.HTML)
