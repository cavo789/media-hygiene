"""`GET`/`POST /api/albums`: the albums, and a page's files added or taken out (0295).

Served by `search`, `browse` and the burst review, apart from *Set aside*
(`/api/chosen`, `/api/decide`): an album never touches the decisions file, and the
files set aside never enter an album. `POST` names the album and the files (their
keys on the page, or every file a search finds: `all`); the answer is read back from
the disk, the files missing from each album said. Nothing is saved when the reports
folder cannot keep it: the page says why.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.views import SearchAsked
from media_hygiene.share.album_cover import choose_cover
from media_hygiene.share.album_said import cover_message, shelf_view
from media_hygiene.share.album_store import AlbumChange

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.share.album_store import AlbumStore, Shelf

ALBUMS_PATH: Final = "/api/albums"
# Files added at once: a search finding more is narrowed first (the TV shows 3000).
MAX_ADDED: Final = 3000
_MAX_TEXT: Final = 200


class AlbumAsked(BaseModel):
    """`POST /api/albums`: add or remove the files picked, or every file found."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["add", "remove", "cover"]  # cover: one file of the album (0371)
    album: str = Field(max_length=_MAX_TEXT)
    keys: tuple[str, ...] = Field(default=(), max_length=MAX_ADDED)
    all: bool = False  # every file the search finds, not only those shown
    search: SearchAsked = SearchAsked()


@dataclass(frozen=True, slots=True)
class AlbumDesk:
    """Answers a page about the albums; one change at a time."""

    store: AlbumStore
    # The files a request names (its keys, or every file found), in the container.
    pick: Callable[[AlbumAsked], tuple[Path, ...]]
    ready: Callable[[], None]  # raises when the reports folder cannot keep them
    _turn: asyncio.Lock = field(default_factory=asyncio.Lock)

    def state(self) -> Response:
        """`GET /api/albums`: every album, read from the disk, its moved files followed.

        Returns:
            The albums and the sentence; 409 for a file that is not an albums file.
        """
        try:
            shelf = self.store.on_disk()
        except MediaHygieneError as exc:
            return _refused(exc)
        except OSError as exc:
            return _not_saved(exc)
        return json_response(HTTPStatus.OK, shelf_view(shelf, None, self._host))

    async def answer(self, body: bytes) -> Response:
        """`POST /api/albums`: save a change, then say what the file holds.

        Args:
            body: The JSON the page sent.

        Returns:
            The albums read back; 400 for a body that is not a change, 409 when
            nothing can be saved.
        """
        try:
            asked = AlbumAsked.model_validate_json(body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        files = self.pick(asked)
        if len(files) > MAX_ADDED:
            message = _(
                "{count} files: an album takes at most {most} at once. Narrow the "
                "search (a year, a folder), then add again."
            ).format(count=len(files), most=MAX_ADDED)
            return json_response(HTTPStatus.CONFLICT, {"error": message})
        change = AlbumChange(asked.album, files)
        async with self._turn:
            try:
                self.ready()
                shelf = await asyncio.to_thread(self._run(asked), change)
            except MediaHygieneError as exc:
                return _refused(exc)
            except OSError as exc:
                return _not_saved(exc)
        said = shelf_view(shelf, asked.album, self._host)
        if asked.action == "cover":
            said["message"] = cover_message(shelf, asked.album)
        return json_response(HTTPStatus.OK, said)

    def _run(self, asked: AlbumAsked) -> Callable[[AlbumChange], Shelf]:
        """The change a request asks for.

        Args:
            asked: The request.

        Returns:
            What saves it.
        """
        if asked.action == "cover":
            return partial(choose_cover, self.store)
        return self.store.add if asked.action == "add" else self.store.remove

    @property
    def _host(self) -> str:
        """The albums file, as the user sees it.

        Returns:
            Its host path.
        """
        return self.store.place.host


def _not_saved(error: OSError) -> Response:
    """Answer that the albums file could not be written.

    Args:
        error: Why.

    Returns:
        409, with the message.
    """
    message = _("Cannot save the albums file: {error}.")
    return _refused(MediaHygieneError(message.format(error=error.strerror or error)))


def _refused(error: MediaHygieneError) -> Response:
    """Answer that nothing was saved, and why.

    Args:
        error: Why.

    Returns:
        409, with the message and its tip.
    """
    said = " ".join(part for part in (error.message, error.tip) if part)
    return json_response(HTTPStatus.CONFLICT, {"error": said})
