"""The actions menu of a person (0836), answered before the people page's own routes.

`POST /api/rename` renames or merges (`rename_desk`), `POST /api/person-aside` sets
aside a person's photos and drops the name (`person_aside`), `GET`/`POST /api/albums`
the albums (`share.album_route`, keys: the board's face numbers, so *Album in memory*
adds every photo of the person). Loopback hosts only, JSON bodies from the page's own
origin, as every page. `/person` answers `rename` only (`person.door`): its naming line
renames; the photos are set aside from the people page.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.people.person_aside import (
    PERSON_ASIDE_PATH,
    PersonAside,
    PersonAsideAsked,
    PersonPhotos,
)
from media_hygiene.people.rename_desk import RenameAsked
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.http import Response, is_local
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.search.chosen_api import chosen_refused

if TYPE_CHECKING:
    from media_hygiene.people.app import PeopleApp
    from media_hygiene.people.rename_desk import RenameDesk
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Request

RENAME_PATH: Final = "/api/rename"


@dataclass(frozen=True, slots=True)
class RenameDoor:
    """A page answering `POST <path>` with its rename desk, anything else itself."""

    app: Handling
    desk: RenameDesk
    path: str = RENAME_PATH

    async def handle(self, request: Request) -> Response:
        """Rename from the loopback; anything else to the page.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.path != self.path:
            return await self.app.handle(request)
        if not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        if request.method != "POST":
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        refused = refused_post(request)
        if refused is not None:
            return refused
        try:
            said = self.desk.answer(RenameAsked.model_validate_json(request.body))
        except (ValueError, OSError) as exc:  # ValidationError included
            return save_refused(exc)
        return json_response(HTTPStatus.OK, said)


@dataclass(frozen=True, slots=True)
class PersonAsideDoor:
    """The people page, answering `POST /api/person-aside` first."""

    app: PeopleApp
    desk: PersonAside

    async def handle(self, request: Request) -> Response:
        """Set aside from the loopback; anything else to the page.

        Args:
            request: The request.

        Returns:
            The response, with the page's state after a change.
        """
        if request.path != PERSON_ASIDE_PATH:
            return await self.app.handle(request)
        if not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        if request.method != "POST":
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        return refused_post(request) or self._act(request)

    def _act(self, request: Request) -> Response:
        """List, set aside, or restore, as the page asks.

        Args:
            request: `POST /api/person-aside`.

        Returns:
            The photos, or the page's state with what the files hold now.
        """
        app = self.app
        view = app.view()
        photos = PersonPhotos(app.roster.board, app.roster.sections(view), view)
        try:
            asked = PersonAsideAsked.model_validate_json(request.body)
            said = self.desk.answer(asked, photos)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        except MediaHygieneError as exc:
            return chosen_refused(exc)
        except (ValueError, OSError) as exc:
            return save_refused(exc)
        if asked.check:
            return json_response(HTTPStatus.OK, said)
        return json_response(HTTPStatus.OK, {**app.state(), "aside": said})
