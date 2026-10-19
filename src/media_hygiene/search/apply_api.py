"""`POST /api/apply`: *Apply now*, on `browse` opened from the home page (0243).

The page ends with the code of the home page's step that applies the decisions
(`clean --decisions`): `STEP_EXIT_BASE + n`, `n` its number in `mh menu`. `mh`, whose
home loop opened the page, then runs that step with its usual question and opens the
home page again: no new code path, the home page's own. Opened by `mh browse` alone,
nobody would run the step: the page shows no button and this route refuses.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.review.home_views import STEP_EXIT_BASE
from media_hygiene.review.serving import json_response

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.ending import Ending
    from media_hygiene.review.http import Response
    from media_hygiene.search.chosen_api import ChosenDesk

APPLY_PATH: Final = "/api/apply"


@dataclass(frozen=True, slots=True)
class ApplyStep:
    """The home page's step that applies the decisions, as `mh menu` numbers it."""

    number: int
    command: str  # the full command, `mh` included, as the home page shows it


@dataclass(frozen=True, slots=True)
class ApplyDesk:
    """Ends the page on the step that applies what is set aside, when `mh` runs it."""

    step: Callable[[], ApplyStep | None] | None  # None: not opened from the home page
    ending: Ending
    chosen: ChosenDesk

    @property
    def offered(self) -> bool:
        """Whether the page may show *Apply now*: opened from the home page.

        Returns:
            True when `mh`'s home loop runs the step the page ends with.
        """
        return self.step is not None

    async def answer(self) -> Response:
        """End the page with the code of the step, read again from the tool folders.

        Returns:
            The step, about to run in the terminal; 409 when the page was not opened
            from the home page, nothing is set aside, or the menu has no such step.
        """
        if self.step is None:
            message = _("Opened without the home page: type the next step yourself.")
            return json_response(HTTPStatus.CONFLICT, {"error": message})
        if not self.chosen.paths():
            return json_response(
                HTTPStatus.CONFLICT, {"error": _("Nothing set aside.")}
            )
        step = await asyncio.to_thread(self.step)
        if step is None:
            message = _(
                "No step applies the decisions now: type the next step yourself."
            )
            return json_response(HTTPStatus.CONFLICT, {"error": message})
        self.ending.end(STEP_EXIT_BASE + step.number)
        return json_response(
            HTTPStatus.OK, {"number": step.number, "command": step.command}
        )
