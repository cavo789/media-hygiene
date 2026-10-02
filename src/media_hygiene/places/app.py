"""The routes of the map page: the page, Leaflet, its state, saving, the town search.

`GET /` serves the page, `GET /leaflet.js` and `/leaflet.css` the vendored library,
`GET /api/state` the places and the clusters; `POST /api/places` saves every place
into `config.toml`, `POST /api/search` finds towns offline, `POST /api/osm` areas
online (`osm_search`). Like `review`: loopback hosts only, JSON bodies only, from the
page's own origin.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.i18n import _
from media_hygiene.places.config_file import PlaceEdit
from media_hygiene.places.osm_search import OSM_PATH, SearchText, search_osm
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.serving import json_response, refused_post, serve_connection

if TYPE_CHECKING:
    import asyncio
    from collections.abc import Mapping

    from media_hygiene.geo.nominatim import Nominatim
    from media_hygiene.places.board import PlacesBoard
    from media_hygiene.review.http import Request

PAGE_PATH: Final = "/"
STATE_PATH: Final = "/api/state"
SAVE_PATH: Final = "/api/places"
SEARCH_PATH: Final = "/api/search"
# Sends only `http://127.0.0.1:<port>` to the tile server, which asks for a referrer.
PAGE_REFERRER: Final = "strict-origin"
# Leaflet from the page's own origin, the tiles from their server only.
PAGE_POLICY: Final = (
    "default-src 'none'; script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' {tiles}; connect-src 'self'; "
    "frame-ancestors 'none'"
)
_GET, _POST = "GET", "POST"
_VALUE_ERROR: Final = "Value error, "


class _PlaceIn(PersonalPlace):
    """A place as the page sends it: its rank in the file, None when new."""

    key: int | None = None


class _Save(BaseModel):
    """`POST /api/places`: every place."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    places: tuple[_PlaceIn, ...]


@dataclass(frozen=True, slots=True)
class PlacesApp:
    """Answers the browser; the board holds the state and saves it.

    `osm` searches OpenStreetMap; None when `[places] nominatim_url` is empty.
    """

    board: PlacesBoard
    page: Response
    assets: Mapping[str, Response]
    osm: Nominatim | None = None

    async def connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Serve one connection: one request, one response.

        Args:
            reader: What the browser sends.
            writer: Where to answer.
        """
        await serve_connection(reader, writer, self.handle)

    async def handle(self, request: Request) -> Response:
        """Route a request.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if not is_local(request):
            message = _("Open the map at 127.0.0.1 or localhost.")
            return Response(HTTPStatus.FORBIDDEN, message.encode())
        path = request.path
        if request.method == _GET:
            return self._get(path)
        if request.method != _POST or path not in {SAVE_PATH, SEARCH_PATH, OSM_PATH}:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        refused = refused_post(request)
        if refused is not None:
            return refused
        if path == OSM_PATH:
            return await search_osm(self.osm, request)
        return self._save(request) if path == SAVE_PATH else self._search(request)

    def _get(self, path: str) -> Response:
        """Serve the page, its state, or Leaflet.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for anything else.
        """
        if path == PAGE_PATH:
            return self.page
        if path == STATE_PATH:
            return json_response(HTTPStatus.OK, self.board.state())
        return self.assets.get(path, Response(HTTPStatus.NOT_FOUND))

    def _save(self, request: Request) -> Response:
        """Save every place into `config.toml`.

        Args:
            request: `POST /api/places`.

        Returns:
            The new state, or an error with a translated message.
        """
        try:
            body = _Save.model_validate_json(request.body)
            edits = [
                PlaceEdit(place.key, PersonalPlace(**place.model_dump(exclude={"key"})))
                for place in body.places
            ]
            self.board.save(edits)
        except ValidationError as exc:
            reasons = "; ".join(
                str(error["msg"]).removeprefix(_VALUE_ERROR) for error in exc.errors()
            )
            message = _("Not saved: {reason}.").format(reason=reasons)
            return json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": message})
        except ValueError as exc:
            message = _("Not saved: {reason}.").format(reason=exc)
            return json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": message})
        except OSError as exc:
            message = _("Cannot save config.toml: {error}.")
            error = message.format(error=exc.strerror or exc)
            return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": error})
        return json_response(HTTPStatus.OK, self.board.state())

    def _search(self, request: Request) -> Response:
        """Find towns by name.

        Args:
            request: `POST /api/search`.

        Returns:
            The towns found.
        """
        try:
            search = SearchText.model_validate_json(request.body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        towns = self.board.search(search.text)
        return Response(HTTPStatus.OK, json.dumps(towns).encode(), ContentType.JSON)
