"""`GET`/`POST /api/chosen`: what is set aside, and the page's choices, saved at once.

`POST` adds the files picked (their keys), or every file the search finds (`all`), or
takes them out (`remove`); the answer is read back from the disk. Nothing is saved
when the reports folder cannot keep it: the page says why.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.chosen import Selection, chosen_size
from media_hygiene.search.views import SearchAsked

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.report.chosen_decisions import ChosenFile
    from media_hygiene.search.chosen import ChosenStore
    from media_hygiene.search.fts import SearchIndex

CHOSEN_PATH: Final = "/api/chosen"
_MAX_KEYS: Final = 100_000


class ChosenAsked(BaseModel):
    """`POST /api/chosen`: add or remove the files picked, or every file found."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["add", "remove"]
    keys: tuple[int, ...] = Field(default=(), max_length=_MAX_KEYS)
    all: bool = False  # every file the search finds, not only those shown
    search: SearchAsked = SearchAsked()


@dataclass(frozen=True, slots=True)
class ChosenDesk:
    """Answers the page about the files set aside."""

    store: ChosenStore
    index: SearchIndex
    ready: Callable[[], None]  # raises when the reports folder cannot keep them

    def paths(self) -> frozenset[str]:
        """The host paths of the files set aside, to mark them on the page.

        Returns:
            Them; none when the file cannot be read.
        """
        try:
            return frozenset(file.path for file in self.store.on_disk())
        except MediaHygieneError:
            return frozenset()

    def state(self) -> Response:
        """`GET /api/chosen`: what the decisions file holds.

        Returns:
            The count, the size and the sentence; 409 for a file that is not a
            decisions file.
        """
        try:
            return self._said(self.store.on_disk())
        except MediaHygieneError as exc:
            return _refused(exc)

    def answer(self, body: bytes) -> Response:
        """`POST /api/chosen`: save a change, then say what the file holds.

        Args:
            body: The JSON the page sent.

        Returns:
            The state read back; 400 for a body that is not a choice, 409 when
            nothing can be saved.
        """
        try:
            asked = ChosenAsked.model_validate_json(body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        if asked.all:
            photos = self.index.versions(asked.search.query())
        else:
            found = (self.index.source_of(key) for key in asked.keys)
            photos = tuple(photo for photo in found if photo is not None)
        try:
            self.ready()
            if asked.action == "remove":
                return self._said(self.store.remove(photos))
            return self._said(
                self.store.add(Selection(photos, asked.search.found_by()))
            )
        except MediaHygieneError as exc:
            return _refused(exc)
        except OSError as exc:
            message = _("Cannot save the decisions file: {error}.")
            return _refused(MediaHygieneError(message.format(error=exc.strerror)))

    def _said(self, files: tuple[ChosenFile, ...]) -> Response:
        """Say how many files are set aside, where, and what moves them.

        Args:
            files: The files set aside, read back from the disk.

        Returns:
            The JSON answer.
        """
        count = len(files)
        size = human_size(chosen_size(files))
        if count:
            message = ngettext(
                "{count} file set aside ({size}), saved in {place}: 'clean "
                "--decisions' moves it to the quarantine.",
                "{count} files set aside ({size}), saved in {place}: 'clean "
                "--decisions' moves them to the quarantine.",
                count,
            ).format(count=human_number(count), size=size, place=self.store.place.host)
        else:
            message = _("Nothing set aside.")
        return json_response(
            HTTPStatus.OK, {"count": count, "size": size, "message": message}
        )


def _refused(error: MediaHygieneError) -> Response:
    """Answer that nothing was saved, and why.

    Args:
        error: Why.

    Returns:
        409, with the message and its tip.
    """
    said = " ".join(part for part in (error.message, error.tip) if part)
    return json_response(HTTPStatus.CONFLICT, {"error": said})
