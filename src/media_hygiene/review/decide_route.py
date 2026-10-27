"""What the reviews of near duplicates, folder pairs and unwanted photos answer alike.

`DecidingApp` routes them: each review only says where it decides, and how.

`GET`: the decisions file, an original, a preview, else the page or its state.
`POST` of a decision: refused without a JSON body; a body that is not a choice is a
400, a refused choice a 422 with its reason, a file that cannot be written a 500.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, ClassVar, Protocol, override

from pydantic import ValidationError

from media_hygiene.errors import DecisionsError, MountError
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.review.files import ReviewFiles, file_response
from media_hygiene.review.http import Response
from media_hygiene.review.local_app import LocalApp, choice_failed, page_or_state
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from concurrent.futures import Executor
    from pathlib import Path

    from pydantic import BaseModel

    from media_hygiene.review.http import Request

_GET, _POST = "GET", "POST"


class ReviewPages(ReviewFiles, Protocol):
    """A review session: its files, and the state its page reads."""

    def state(self) -> BaseModel:
        """Describe everything the page shows.

        Returns:
            The state.
        """


async def read_route(
    request: Request, session: ReviewPages, pages: tuple[bytes, PreviewPool]
) -> Response:
    """Answer a `GET`: a file of the review, else the page or its state.

    Args:
        request: The request.
        session: The review.
        pages: The page, and the worker pool with the previews' cache folder.

    Returns:
        The response; 404 for an unknown path.
    """
    page, pool = pages
    found = await file_response(request.path, session, pool)
    if found is not None:
        return found
    return page_or_state(request.path, page, session.state)


def decide_route(
    request: Request, decide: Callable[[bytes], Mapping[str, object]]
) -> Response:
    """Answer the `POST` of a decision.

    Args:
        request: The request, with a JSON body.
        decide: Reads the body, records and saves the choices, and returns the
            counts and the file as read back from the disk; raises `ValidationError`
            for a body that is not a choice, `DecisionsError` for a refused one,
            `MountError` when the reports folder cannot keep the file.

    Returns:
        The response.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    try:
        answer = decide(request.body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    except (DecisionsError, MountError, OSError) as exc:
        return choice_failed(exc)
    return json_response(HTTPStatus.OK, dict(answer))


@dataclass(frozen=True, slots=True)
class DecidingApp[S: ReviewPages](LocalApp):
    """Answers the browser for one review; the session holds and saves the choices."""

    decide_path: ClassVar[str]  # where the page posts its choices
    session: S
    page: bytes
    executor: Executor
    previews: Path | None = None  # the cache folder of previews, if any

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.method == _GET:
            pool = PreviewPool(self.executor, self.previews)
            return await read_route(request, self.session, (self.page, pool))
        if request.path == self.decide_path and request.method == _POST:
            return decide_route(request, self.decide)
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)

    @abstractmethod
    def decide(self, body: bytes) -> Mapping[str, object]:
        """Record the choices of a JSON body, save them, read the file back.

        Args:
            body: The body the page posted.

        Returns:
            The counts, and the file as read back from the disk.
        """
