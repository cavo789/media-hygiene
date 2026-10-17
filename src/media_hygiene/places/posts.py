"""The changes the map page posts to the board; each answers the state read back.

`POST /api/places` saves every place; `POST /api/aside` sets a cluster aside or
restores it (0234); `POST /api/place-photos` gives a cluster's photos to a place, or
takes one back (0237): it reads the photos to hash them, off the server's loop.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.config.places_settings import IgnoredSpot
from media_hygiene.places.config_file import PlaceEdit
from media_hygiene.places.hand_desk import PhotosAct
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.serving import json_response

if TYPE_CHECKING:
    from media_hygiene.places.board import PlacesBoard
    from media_hygiene.review.http import Request, Response

SAVE_PATH: Final = "/api/places"
ASIDE_PATH: Final = "/api/aside"
PHOTOS_PATH: Final = "/api/place-photos"
BOARD_POSTS: Final = frozenset({SAVE_PATH, ASIDE_PATH, PHOTOS_PATH})


class _PlaceIn(PersonalPlace):
    """A place as the page sends it: its rank in the file, None when new."""

    key: int | None = None


class _Save(BaseModel):
    """`POST /api/places`: every place."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    places: tuple[_PlaceIn, ...]


class _Aside(BaseModel):
    """`POST /api/aside`: a cluster's middle, or a circle's to restore."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    restore: bool = False


async def board_post(board: PlacesBoard, request: Request) -> Response:
    """Apply a change the page posts, then answer the state read back.

    Args:
        board: The map's state.
        request: One of `BOARD_POSTS`.

    Returns:
        The new state, or an error with a translated message.
    """
    try:
        if request.path == SAVE_PATH:
            body = _Save.model_validate_json(request.body)
            edits = [
                PlaceEdit(place.key, PersonalPlace(**place.model_dump(exclude={"key"})))
                for place in body.places
            ]
            board.save(edits)
        elif request.path == ASIDE_PATH:
            aside = _Aside.model_validate_json(request.body)
            spot = IgnoredSpot(latitude=aside.latitude, longitude=aside.longitude)
            (board.restore if aside.restore else board.set_aside)(spot)
        else:
            act = PhotosAct.model_validate_json(request.body)
            await asyncio.to_thread(board.place_photos, act)
    except (ValueError, OSError) as exc:  # ValidationError included
        return save_refused(exc)
    return json_response(HTTPStatus.OK, board.state())
