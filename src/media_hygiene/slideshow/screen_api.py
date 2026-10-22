"""What the TV asks: `GET /api/wait/<version>`, the picture to show once it changes.

A TV not paired yet gets its code to show at once, then asks `/api/wait/code`: that
answer waits for a change (a TV paired, the show moving) and says the code again until
a phone types it; the next answer is then the show. A token the server does not know
(the server restarted) gets 401: the screen page reloads, and gets a new code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response
from media_hygiene.slideshow.desk import WAIT_SECONDS
from media_hygiene.slideshow.door import Visitor
from media_hygiene.slideshow.pictures import tv_path
from media_hygiene.slideshow.screens import shown_code

if TYPE_CHECKING:
    from media_hygiene.review.http import Request, Response
    from media_hygiene.slideshow.desk import Desk

WAIT_PREFIX: Final = "/api/wait/"
CODE_SHOWN: Final = "code"  # `/api/wait/code`: the TV shows its code, waits for a phone


@dataclass(frozen=True, slots=True)
class ScreenDesk:
    """Answers one TV's question."""

    desk: Desk
    visitor: Visitor
    token: str  # the TV's cookie, empty without one

    async def answer(self, request: Request) -> Response | None:
        """Answer `GET /api/wait/<version>`, once the show is past that version.

        Args:
            request: The request.

        Returns:
            The TV's picture, the next one and the version; the code to show while
            not paired; None for another route.
        """
        if request.method != "GET" or not request.path.startswith(WAIT_PREFIX):
            return None
        since = request.path.removeprefix(WAIT_PREFIX)
        screens = self.desk.screens
        if self.visitor is Visitor.STRANGER:
            if screens.code_of(self.token) is None:
                return json_response(HTTPStatus.UNAUTHORIZED, {"code": ""})
            if since == CODE_SHOWN:  # the code is on the TV: wait for a phone
                await self.desk.changes.wait(WAIT_SECONDS)
            code = screens.code_of(self.token)
            if code is not None:
                return json_response(HTTPStatus.OK, {"code": shown_code(code)})
        await self.desk.settle(int(since) if since.isdigit() else 0)
        return json_response(HTTPStatus.OK, screen_view(self.desk))


def screen_view(desk: Desk) -> dict[str, object]:
    """What the TV shows: never a name, never a path.

    Args:
        desk: The show.

    Returns:
        The version, the picture shown and the next one (empty for none).
    """
    show = desk.show
    current, upcoming = show.current, show.upcoming
    return {
        "version": show.version,
        "photo": "" if current is None else tv_path(current.key),
        "next": "" if upcoming is None else tv_path(upcoming.key),
        "code": "",
    }


def pair_screen(desk: Desk, body: bytes) -> Response:
    """Pair the TV showing the code typed on the phone (`POST /api/screens`).

    Args:
        desk: The show and its TVs.
        body: `{"code": "123 456"}`.

    Returns:
        The show; 422 with the reason when no TV shows that code.
    """
    screens = desk.screens
    if screens.confirm(typed_code(body)):
        desk.show.version += 1  # the remotes say one TV more
        desk.changes.notify()  # the TV waiting gets the show
        return json_response(HTTPStatus.OK, desk.state())
    error = _("No TV shows this code: type the code the TV shows now.")
    if screens.closed:
        error = _(
            "Too many wrong codes: pairing a TV is closed. Stop the slideshow "
            "(Ctrl+C on the PC), then start it again."
        )
    return json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": error})


def typed_code(body: bytes) -> str:
    """Read the code a TV shows, as typed on the phone.

    Args:
        body: The JSON the page sent: `{"code": "123 456"}`.

    Returns:
        The code; empty for a body that holds none.
    """
    try:
        value = json.loads(body)
    except ValueError:
        return ""
    code = value.get("code") if isinstance(value, dict) else None
    return code if isinstance(code, str) else ""
