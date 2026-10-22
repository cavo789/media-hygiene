"""What the TV asks: `GET /api/wait/<version>`, the picture to show once it changes.

A TV not paired yet gets its code to show at once, then asks `/api/wait/code`: that
answer waits for a change (a TV paired, the show moving) and says the code again until
a phone types it; the next answer is then the show. A token the server does not know
(the server restarted) gets 401: the screen page reloads, and gets a new code.

A TV whose browser plays no video asks `/api/wait/<version>/photos` (0292); a TV that
played a video to its end (or failed to) says so: `GET /api/ended/<key>`, and the
show moves on. A `GET`, as everything the TV asks: it moves the show only while
that video is shown.
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
from media_hygiene.slideshow.films import film_ended, film_path, show_films
from media_hygiene.slideshow.pictures import tv_path
from media_hygiene.slideshow.screens import shown_code

if TYPE_CHECKING:
    from media_hygiene.review.http import Request, Response
    from media_hygiene.slideshow.desk import Desk

WAIT_PREFIX: Final = "/api/wait/"
CODE_SHOWN: Final = "code"  # `/api/wait/code`: the TV shows its code, waits for a phone
PHOTOS_ONLY: Final = "/photos"  # `/api/wait/<version>/photos`: a TV playing no video
ENDED_PREFIX: Final = "/api/ended/"
_PLAYERS: Final = frozenset({Visitor.SCREEN, Visitor.PC})  # who plays the videos


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
        if request.method != "GET":
            return None
        if request.path.startswith(ENDED_PREFIX) and self.visitor in _PLAYERS:
            return self._ended(request.path.removeprefix(ENDED_PREFIX))
        if not request.path.startswith(WAIT_PREFIX):
            return None
        asked = request.path.removeprefix(WAIT_PREFIX)
        since = asked.removesuffix(PHOTOS_ONLY)
        screens = self.desk.screens
        if self.visitor is Visitor.STRANGER:
            if screens.code_of(self.token) is None:
                return json_response(HTTPStatus.UNAUTHORIZED, {"code": ""})
            if since == CODE_SHOWN:  # the code is on the TV: wait for a phone
                await self.desk.changes.wait(WAIT_SECONDS)
            code = screens.code_of(self.token)
            if code is not None:
                return json_response(HTTPStatus.OK, {"code": shown_code(code)})
        self._films(films=since == asked)
        await self.desk.settle(int(since) if since.isdigit() else 0)
        return json_response(HTTPStatus.OK, screen_view(self.desk))

    def _ended(self, key: str) -> Response:
        """The TV played a video to its end: move on.

        Args:
            key: The video's key, from the path.

        Returns:
            What the TV shows now.
        """
        if key.isdigit() and film_ended(self.desk.show, int(key)):
            self.desk.changes.notify()
        return json_response(HTTPStatus.OK, screen_view(self.desk))

    def _films(self, *, films: bool) -> None:
        """Record whether a TV paired plays videos; the show follows its TVs.

        Args:
            films: False for a TV whose browser plays no video.
        """
        if self.visitor is not Visitor.SCREEN:
            return
        screens, show = self.desk.screens, self.desk.show
        screens.tell(self.token, films=films)
        if screens.films != show.films:
            show_films(show, films=screens.films)
            self.desk.changes.notify()


def screen_view(desk: Desk) -> dict[str, object]:
    """What the TV shows: never a name, never a path.

    Args:
        desk: The show.

    Returns:
        The version, the key, the picture or the video shown, the next picture
        to load (empty for none), whether the show plays.
    """
    show = desk.show
    current, upcoming = show.current, show.upcoming
    return {
        "version": show.version,
        "key": None if current is None else current.key,
        "photo": "" if current is None or current.film else tv_path(current.key),
        "film": "" if current is None else film_path(current),
        "next": "" if upcoming is None or upcoming.film else tv_path(upcoming.key),
        "playing": show.playing,
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
