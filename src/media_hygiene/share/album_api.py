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

    action: Literal["add", "remove", "cover", "tv"]  # cover: one file (0371); tv: 0454
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
    # 📺 *On the TV* (0454): the files shown by the home server's slideshow.
    tv: Callable[[tuple[Path, ...]], Response] | None = None
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
        early = self._early(asked, files)
        if early is not None:
            return early
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

    def _early(self, asked: AlbumAsked, files: tuple[Path, ...]) -> Response | None:
        """The answer before any save: too many files, or the TV (0454).

        Args:
            asked: The request.
            files: The files it names.

        Returns:
            409 for too many, the TV's answer; None to save a change.
        """
        early = too_many(files)
        if early is not None or asked.action != "tv":
            return early
        return Response(HTTPStatus.NOT_FOUND) if self.tv is None else self.tv(files)

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


def too_many(files: tuple[Path, ...]) -> Response | None:
    """Refuse more files than an album, or the TV, takes at once.

    Args:
        files: The files a request names.

    Returns:
        409 with the way to narrow the search; None when they fit.
    """
    if len(files) <= MAX_ADDED:
        return None
    message = _(
        "{count} files: an album takes at most {most} at once. Narrow the "
        "search (a year, a folder), then add again."
    ).format(count=len(files), most=MAX_ADDED)
    return json_response(HTTPStatus.CONFLICT, {"error": message})


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
