"""`POST /api/apply`: *Apply now*, on a page opened from the home page (0243, 0288).

The page ends with the code of the home page's step that applies the decisions
(`clean --decisions`): `STEP_EXIT_BASE + n`, `n` its number in `mh menu`. `mh`, whose
home loop opened the page, then runs that step with its usual question and opens the
home page again: no new code path, the home page's own. Opened by its command alone,
nobody would run the step: the page shows no button and this route refuses.
`browse` routes it itself; the reviews wrap their app in `ApplyingApp`.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ExitCode
from media_hygiene.i18n import _
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.home_views import STEP_EXIT_BASE
from media_hygiene.review.http import Response, is_local
from media_hygiene.review.presence import Presence
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Request

APPLY_PATH: Final = "/api/apply"
_POST: Final = "POST"


@dataclass(frozen=True, slots=True)
class ApplyStep:
    """The home page's step that applies the decisions, as `mh menu` numbers it."""

    number: int
    command: str  # the full command, `mh` included, as the home page shows it


@dataclass(frozen=True, slots=True)
class ApplyOffer:
    """What *Apply now* needs from a page: the step, and whether anything is chosen."""

    step: Callable[[], ApplyStep | None] | None  # None: not opened from the home page
    pending: Callable[[], bool]  # something is set aside (or decided) in the file


@dataclass(frozen=True, slots=True)
class ReviewStart:
    """The port of a review page, and the step its *Apply now* ends on."""

    port: int
    apply: Callable[[], ApplyStep | None] | None = None  # None: no button


@dataclass(frozen=True, slots=True)
class ApplyDesk:
    """Ends the page on the step that applies what is set aside, when `mh` runs it."""

    offer: ApplyOffer
    ending: Ending

    @property
    def offered(self) -> bool:
        """Whether the page may show *Apply now*: opened from the home page.

        Returns:
            True when `mh`'s home loop runs the step the page ends with.
        """
        return self.offer.step is not None

    async def answer(self) -> Response:
        """End the page with the code of the step, read again from the tool folders.

        Returns:
            The step, about to run in the terminal; 409 when the page was not opened
            from the home page, nothing is set aside, or the menu has no such step.
        """
        if self.offer.step is None:
            message = _("Opened without the home page: type the next step yourself.")
            return json_response(HTTPStatus.CONFLICT, {"error": message})
        if not self.offer.pending():
            return json_response(
                HTTPStatus.CONFLICT, {"error": _("Nothing set aside.")}
            )
        step = await asyncio.to_thread(self.offer.step)
        if step is None:
            message = _(
                "No step applies the decisions now: type the next step yourself."
            )
            return json_response(HTTPStatus.CONFLICT, {"error": message})
        self.ending.end(STEP_EXIT_BASE + step.number)
        return json_response(
            HTTPStatus.OK, {"number": step.number, "command": step.command}
        )


@dataclass(frozen=True, slots=True)
class ApplyingApp:
    """A review's app, answering `POST /api/apply` before it."""

    app: Handling
    desk: ApplyDesk

    async def handle(self, request: Request) -> Response:
        """Answer *Apply now* from the page itself; anything else goes to the app.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.path != APPLY_PATH:
            return await self.app.handle(request)
        if not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        if request.method != _POST:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        return refused_post(request) or await self.desk.answer()


def applying_door(app: Handling, offer: ApplyOffer) -> EndingDoor:
    """The door of a review page: Ctrl+C, its tab closed, home, or *Apply now*.

    Args:
        app: Answers the page.
        offer: The step *Apply now* ends on, and whether anything is chosen.

    Returns:
        The door to serve, until its page asks to end.
    """
    ending = Ending()
    presence = Presence(ending, ExitCode.PAGE_CLOSED)
    return EndingDoor(ApplyingApp(app, ApplyDesk(offer, ending)), ending, presence)
