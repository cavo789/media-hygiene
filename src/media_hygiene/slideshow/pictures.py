"""The pictures of the show: the phone's thumbnails, the TV's pictures. Its photos only.

`/thumb/<key>.jpg` is the grid's thumbnail of `search` (kept in the cache folder);
`/tv/<key>.jpg` the TV's picture (`screen_jpeg`). Only the keys of the show are
answered: a phone or a TV never reaches another photo of the library, nor any
original.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Response
from media_hygiene.review.local_app import jpeg_response
from media_hygiene.search.views import JPEG, THUMB_PREFIX

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.search.pictures import Pictures
    from media_hygiene.slideshow.desk import Desk
    from media_hygiene.slideshow.screen_jpeg import ScreenJob

TV_PREFIX: Final = "/tv/"


def tv_path(key: int) -> str:
    """The address of a photo's TV picture.

    Args:
        key: The photo's key.

    Returns:
        E.g. `/tv/12.jpg`.
    """
    return f"{TV_PREFIX}{key}{JPEG}"


def thumb_path(key: int) -> str:
    """The address of a photo's thumbnail.

    Args:
        key: The photo's key.

    Returns:
        E.g. `/thumb/12.jpg`.
    """
    return f"{THUMB_PREFIX}{key}{JPEG}"


def slides_view(desk: Desk) -> dict[str, object]:
    """The photos of the show, for the phone's grid.

    Args:
        desk: The show.

    Returns:
        Each photo's key, thumbnail and day.
    """
    slides = [
        {"key": slide.key, "thumb": thumb_path(slide.key), "day": slide.day}
        for slide in desk.show.slides
    ]
    return {"slides": slides}


@dataclass(frozen=True, slots=True)
class ShowPictures:
    """Makes the pictures of the show's photos, in the worker pool."""

    keys: frozenset[int]
    thumbs: Pictures  # the search's: thumbnails kept in the cache folder
    screen: ScreenJob
    executor: Executor

    async def answer(self, path: str, *, tv_only: bool = False) -> Response | None:
        """Serve a thumbnail or a TV picture of the show.

        Args:
            path: The path asked for.
            tv_only: A TV asks: its pictures only.

        Returns:
            The JPEG (404 for a photo not in the show, or one that cannot be shown);
            None when the path names no picture.
        """
        prefixes = (TV_PREFIX,) if tv_only else (TV_PREFIX, THUMB_PREFIX)
        prefix = next((start for start in prefixes if path.startswith(start)), None)
        if prefix is None or not path.endswith(JPEG):
            return None
        key = path.removeprefix(prefix).removesuffix(JPEG)
        if not key.isdigit() or int(key) not in self.keys:
            return Response(HTTPStatus.NOT_FOUND)
        if prefix == THUMB_PREFIX:
            return await self.thumbs.answer(path)
        photo = self.thumbs.source(key)
        if photo is None:
            return Response(HTTPStatus.NOT_FOUND)
        return await jpeg_response(self.executor, self.screen.renderer(), photo)
