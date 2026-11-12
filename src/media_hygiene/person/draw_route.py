"""`POST /person/api/draw`: a face drawn by hand on the photo of `/person` (TODO 0715).

Without a box, the page asks for the photo to draw on: its preview, by a number of the
shelf. With one (fractions of the upright photo), the worker pool looks for the face
there (`drawing`); a usable face is kept in the index, flagged drawn (`drawn_faces`),
and handed to the page like a detected one: it is named and searched the same way.
Nothing usable, nothing is written: the page says so in one sentence.
"""

from __future__ import annotations

import asyncio
import sqlite3
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.i18n import _
from media_hygiene.index.drawn_faces import add_drawn
from media_hygiene.index.repository import FactsRepository
from media_hygiene.person.drawing import DrawJob, draw_face
from media_hygiene.person.finding import face_view
from media_hygiene.person.routes import JPEG, PREVIEW_PREFIX
from media_hygiene.person.shelf import ShelfFace

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.person.app import PersonApp
    from media_hygiene.person.drawing import Drawn

_PATH_LENGTH: Final = 4096
_NO_PICTURE: Final = b""  # a photo on the shelf to show only: no face to search


class DrawAsked(BaseModel):
    """A photo, and the box drawn on it, if any (fractions of the photo)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = Field(min_length=1, max_length=_PATH_LENGTH)
    box: tuple[float, float, float, float] | None = None

    def fractions(self) -> tuple[float, float, float, float] | None:
        """The box, inside the photo.

        Returns:
            x, y, width, height from 0 to 1; None without a box or an empty one.
        """
        box = self.box
        if box is None:
            return None
        # pylint: disable-next=not-an-iterable  # a tuple once validated
        x, y, wide, high = (min(1.0, max(0.0, value)) for value in box)
        wide, high = min(wide, 1 - x), min(high, 1 - y)
        return (x, y, wide, high) if wide > 0 and high > 0 else None


def _too_small() -> dict[str, object]:
    """Nothing usable in the box: one sentence, nothing written.

    Returns:
        The answer.
    """
    said = _(
        "Too small or blurred to find others: draw the box closer around the face."
    )
    return {"faces": [], "said": said}


async def drawn(app: PersonApp, body: bytes) -> dict[str, object]:
    """Answer the page: the photo to draw on, or the face drawn.

    Args:
        app: The page.
        body: The JSON sent.

    Returns:
        `picture` to draw on, or the face kept, or a sentence (`said`).

    Raises:
        ValidationError: The body is not the question.
    """
    asked = DrawAsked.model_validate_json(body)
    finder = app.finder
    path = finder.place.resolve(asked.path)
    if path is None:
        return finder.photo(asked.path)  # it says why
    box = asked.fractions()
    if asked.box is None:
        key = finder.shelf.add(ShelfFace(path, _NO_PICTURE))
        return {"picture": f"{PREVIEW_PREFIX}{key}{JPEG}"}
    recipe = app.recipe()
    if recipe is None:
        said = _("The face models are not in the cache yet: run 'audit --people' once.")
        return {"faces": [], "said": said}
    if box is None:
        return _too_small()
    loop = asyncio.get_running_loop()
    found = await loop.run_in_executor(
        app.executor, draw_face, DrawJob(path, box, recipe)
    )
    if found is None:
        return _too_small()
    return _kept(app, path, found)


def _kept(app: PersonApp, path: Path, found: Drawn) -> dict[str, object]:
    """Keep a face drawn in the index, then hand it to the page.

    A face too blurred to find others is kept all the same, to be named on its photo:
    the page then names it without searching (`namedOnly`).

    Args:
        app: The page.
        path: Its photo, in the container.
        found: The face, and whether it can find others.

    Returns:
        The face, numbered; a sentence when the index cannot keep it.
    """
    face = found.face
    index = app.finder.faces
    number = None
    if index.file is not None:
        try:
            with FactsRepository.open(index.file) as repository:
                number = add_drawn(repository.connection, index.model, (path, face))
        except sqlite3.Error:
            number = None
    if number is None:
        said = _("This photo is not in the index yet: run 'audit --people' first.")
        return {"faces": [], "said": said}
    index.refresh()
    shelf = app.finder.shelf
    vector = face.embedding if found.searchable else _NO_PICTURE
    key = shelf.add(ShelfFace(path, vector, face.box, number=number))
    if found.searchable:
        return {"faces": [face_view(key)], "drawn": True}
    said = _(
        "Too blurred to find their other photos: "
        "name it, it counts for this photo only."
    )
    return {"faces": [face_view(key)], "drawn": True, "namedOnly": True, "said": said}
