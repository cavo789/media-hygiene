"""A page's presence: its server ends once no tab shows it any more (0261).

A user closes the browser tab, not the PowerShell window: before, the page kept running
there, holding the port and the prompt, until Ctrl+C. The page says it is alive every
few seconds while open, and that it leaves on `pagehide` (a `keepalive` fetch, which
outlives the tab). The server ends a while after a tab left without another coming back
(a reload leaves, then comes back at once), or after a long silence: browsers slow the
timers of a tab in the background (down to once a minute), which must not count as
closed. Nothing ends before a first tab spoke: a page opened late is still served.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from media_hygiene.review.ending import Ending
    from media_hygiene.review.http import Request

PRESENCE_PATH: Final = "/api/alive"
# How often an open page says it is alive (the page's timer; a constant: UI timing).
ALIVE_SECONDS: Final = 10
# After a tab said it leaves: a reload comes back well within it.
LEAVING_GRACE_SECONDS: Final = 10.0
# No news at all: longer than the once-a-minute timers of a tab in the background.
SILENCE_SECONDS: Final = 180.0


class _Alive(BaseModel):
    """`POST /api/alive`: the page is open, or about to leave."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    leaving: bool = False


class Presence:
    """Ends the server with a code once no tab shows the page; remembers it did."""

    __slots__ = ("_code", "_ending", "_timer", "closed")

    def __init__(self, ending: Ending, code: int) -> None:
        """Wait for a first tab before counting anything.

        Args:
            ending: Ends the server.
            code: The exit code once no tab shows the page.
        """
        self._ending = ending
        self._code = code
        self._timer: asyncio.TimerHandle | None = None
        self.closed = False

    def seen(self, *, leaving: bool) -> None:
        """A tab spoke: wait again, briefly when it leaves, long when it is open.

        Args:
            leaving: The tab is going away (closed, reloaded, navigated off).
        """
        if self._timer is not None:
            self._timer.cancel()
        delay = LEAVING_GRACE_SECONDS if leaving else SILENCE_SECONDS
        self._timer = asyncio.get_running_loop().call_later(delay, self._close)

    def _close(self) -> None:
        """No tab came back: end the server, unless something else ended it first."""
        if self._ending.asked is None:
            self.closed = True
            self._ending.end(self._code)


async def presence_response(presence: Presence, request: Request) -> Response:
    """Answer `POST /api/alive`.

    Args:
        presence: The page's presence.
        request: The request, from the loopback.

    Returns:
        200; 400 for a body that is not `{"leaving": <bool>}`.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    try:
        alive = _Alive.model_validate_json(request.body or b"{}")
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    presence.seen(leaving=alive.leaving)
    return json_response(HTTPStatus.OK, {"leaving": alive.leaving})
