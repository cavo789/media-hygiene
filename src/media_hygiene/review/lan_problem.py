"""Why a phone of the home network cannot open the home page, said on the page (0367).

`mh` opens the home page to the home network by default (`[review] lan`). It never stops
because of the network: without an address on a home network, the page opens for the PC
alone; on a network Windows counts as public, its firewall blocks the phone. `mh` tells
the page which (`MEDIA_HYGIENE_LAUNCHER_LAN_PROBLEM`), and the page's card says it in
plain words, never the PowerShell window the user does not read.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import ContentType, is_local
from media_hygiene.review.lan_app import LAN_PATH
from media_hygiene.review.serving import json_response
from media_hygiene.services.next_command import LAUNCHER_VARIABLE

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Request, Response

LAN_PROBLEM_VARIABLE: Final = f"{LAUNCHER_VARIABLE}_LAN_PROBLEM"


class LanProblem(StrEnum):
    """What keeps a phone away, as `mh` found it."""

    NONE = "none"  # no address on a home network: the page stays on the PC
    PUBLIC = "public"  # Windows counts the network as public: its firewall blocks


def lan_problem() -> LanProblem | None:
    """The problem `mh` found, from its environment.

    Returns:
        It; None when there is none, or an unknown word.
    """
    given = os.environ.get(LAN_PROBLEM_VARIABLE, "").strip()
    return next((problem for problem in LanProblem if problem.value == given), None)


@dataclass(frozen=True, slots=True)
class ProblemApp:
    """The home page, its `GET /api/lan` telling the PC's page the problem too."""

    inner: Handling
    problem: LanProblem

    async def handle(self, request: Request) -> Response:
        """Add the problem to the PC's `GET /api/lan`; pass everything else on.

        Args:
            request: The request.

        Returns:
            The response; for the PC's `/api/lan`, the card's data with `problem`.
        """
        answer = await self.inner.handle(request)
        if request.path != LAN_PATH or not is_local(request):
            return answer
        card: dict[str, object] = {}
        if answer.status is HTTPStatus.OK and answer.content_type is ContentType.JSON:
            card = json.loads(answer.body)
        return json_response(HTTPStatus.OK, {**card, "problem": self.problem.value})


def with_problem(handler: Handling) -> Handling:
    """Wrap the home page when `mh` found a problem with the home network.

    Args:
        handler: The home page, opened to the home network or not.

    Returns:
        The handler, wrapped only when there is a problem to say.
    """
    problem = lan_problem()
    return handler if problem is None else ProblemApp(handler, problem)
