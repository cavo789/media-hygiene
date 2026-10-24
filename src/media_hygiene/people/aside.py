"""`POST /api/aside`: set aside every photo of a group of faces, or take them back.

The page sends the faces it shows of one group, every one of them, those taken out by
their cross left out: each of their photos is set aside once, others on it or not (to
forget someone is to remove the photos they are on). Saved like `search` and `browse`
do, in the `chosen` key of the decisions file, read back from the disk; the next
`clean --decisions` moves them to the quarantine, `undo` brings them back. The faces
sent are remembered in the cache (`remembered`, TODO 0328): a new person, or one set
aside before (`into`) when the page sends faces that look like them; taken back, they
are forgotten.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.index.aside_faces import AsideFaces
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.people.remembered import new_aside
from media_hygiene.review.http import Response
from media_hygiene.search.chosen import Selection
from media_hygiene.search.chosen_api import chosen_refused, chosen_said, chosen_unsaved

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.people.remembered import AsideMemory
    from media_hygiene.search.chosen import ChosenStore

ASIDE_PATH: Final = "/api/aside"
_MAX_FACES: Final = 100_000
_LABEL_LENGTH: Final = 100
_ID_LENGTH: Final = 40


class NumberedFace(Protocol):
    """A face a page shows: its photo and its vector."""

    @property
    def path(self) -> Path:
        """The photo, in the container."""

    @property
    def embedding(self) -> bytes:
        """The face's vector."""


class FaceNumbers(Protocol):
    """The faces of a page by number: the people page's board, `/person`'s shelf."""

    def face(self, key: str) -> NumberedFace | None:
        """The face a number names.

        Args:
            key: The number, from the page.
        """


class AsideAsked(BaseModel):
    """What the page asks: set aside, or take back, the photos of these faces."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["add", "remove"]
    faces: tuple[int, ...] = Field(min_length=1, max_length=_MAX_FACES)
    label: str = Field(default="", max_length=_LABEL_LENGTH)  # the group, as shown
    remember: bool = True  # False: one photo, its faces not someone's (TODO 0329)
    into: str = Field(default="", max_length=_ID_LENGTH)  # empty: a new person


@dataclass(frozen=True, slots=True)
class AsideDesk:
    """Saves the photos of a group into the decisions file, checked writable first."""

    store: ChosenStore
    ready: Callable[[], None]  # raises when the reports folder cannot keep them
    memory: AsideMemory | None = None  # None: no persistent cache to remember faces

    def paths(self) -> frozenset[str]:
        """The host paths of the files set aside, to count them on the page.

        Returns:
            Them; none when the file cannot be read.
        """
        return self.store.paths()

    def answer(self, board: FaceNumbers, body: bytes) -> dict[str, object] | Response:
        """Save what the page asks, or say why nothing was saved.

        Args:
            board: The faces of the page.
            body: The JSON the page sent.

        Returns:
            What the decisions file holds now; 400 for a body that is not a choice,
            409 when nothing can be saved.
        """
        try:
            return self.change(board, AsideAsked.model_validate_json(body))
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        except MediaHygieneError as exc:
            return chosen_refused(exc)
        except OSError as exc:
            return chosen_unsaved(exc)

    def change(self, board: FaceNumbers, asked: AsideAsked) -> dict[str, object]:
        """Set aside, or take back, the photos of the faces, then read the file back.

        Args:
            board: The faces of the page.
            asked: What the page asks.

        Returns:
            The count, the size and the sentence, read back from the disk.

        Raises:
            MediaHygieneError: The reports folder cannot keep the file, or it is not
                a decisions file.
            OSError: It cannot be written.
        """
        faces = [face for key in asked.faces if (face := board.face(str(key)))]
        paths = {face.path for face in faces}
        self.ready()
        if asked.action == "remove":
            gone = (PhotoVersion(path, 0, 0) for path in paths)
            said = chosen_said(self.store.remove(gone), self.store.place.host)
            if self.memory is not None:
                self.memory.forget(face.embedding for face in faces)
            return said
        photos = tuple(version for path in sorted(paths) if (version := _version(path)))
        saved = self.store.add(Selection(photos, asked.label.strip()))
        said = chosen_said(saved, self.store.place.host)
        if self.memory is None or not asked.remember:
            return said
        vectors = tuple(face.embedding for face in faces)
        person = AsideFaces(asked.into or new_aside(), asked.label.strip(), vectors)
        remembered = self.memory.remember(person)
        return {**said, "remembered": remembered, "person": person.aside}


def _version(path: Path) -> PhotoVersion | None:
    """The photo as it is now on the disk: `clean` leaves it if it changes after.

    Args:
        path: The photo, in the container.

    Returns:
        Its version; None when it is gone (moved, or deleted).
    """
    try:
        status = path.stat()
    except FileNotFoundError:
        return None
    return PhotoVersion(path, status.st_size, status.st_mtime_ns)
