"""`POST /api/osm`: search OpenStreetMap for an area by its name, on a click only.

The tool asks Nominatim itself, the browser never does: the page's Content-Security-
Policy stays as it is. Only the text typed leaves the computer.
"""

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus
from importlib.metadata import version
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import NominatimError
from media_hygiene.geo.nominatim import Nominatim, Service
from media_hygiene.i18n import active_locale
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response

if TYPE_CHECKING:
    from media_hygiene.review.http import Request

OSM_PATH: Final = "/api/osm"
MAX_TEXT: Final = 100
DISTRIBUTION: Final = "media-hygiene"
HOME_PAGE: Final = "https://github.com/cavo789/media-hygiene"


class SearchText(BaseModel):
    """A search: the text the user typed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = Field(min_length=1, max_length=MAX_TEXT)


def online_search(url: str) -> Nominatim | None:
    """The online search `[places] nominatim_url` names.

    Args:
        url: The address of a Nominatim instance; empty: none.

    Returns:
        The search, in the interface's language, under an identifying User-Agent;
        None without an address.
    """
    if not url:
        return None
    agent = f"{DISTRIBUTION}/{version(DISTRIBUTION)} (+{HOME_PAGE})"
    return Nominatim(Service(url, active_locale().value, agent))


async def search_osm(osm: Nominatim | None, request: Request) -> Response:
    """Find the areas a name designates.

    Args:
        osm: The online search; None when `[places] nominatim_url` is empty.
        request: `POST /api/osm`.

    Returns:
        The areas and how many were too large to list, or an error with a
        translated message; 404 without an online search.
    """
    if osm is None:
        return Response(HTTPStatus.NOT_FOUND)
    try:
        search = SearchText.model_validate_json(request.body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    try:
        found = await osm.search(search.text)
    except NominatimError as exc:
        return json_response(HTTPStatus.BAD_GATEWAY, {"error": exc.message})
    return json_response(
        HTTPStatus.OK,
        {
            "areas": [asdict(area) for area in found.areas],
            "too_large": found.too_large,
        },
    )
