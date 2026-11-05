"""`POST /api/date`: a day given to the photos picked, in their sidecars (0531).

*📅 Date…* in the bar proposes days (the folder's name, the neighbours'), then writes
the day chosen into each photo's `.xmp` sidecar: journaled, undone by `undo`, the photo
never changed. The answer counts what the sidecars say once read back, never what was
asked. A file with its own date, set aside, or in a protected folder is left, and said.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import date
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import ngettext
from media_hygiene.review.serving import json_response
from media_hygiene.search.aside_filter import AsideFilter
from media_hygiene.search.date_propose import proposals
from media_hygiene.search.days import media_day
from media_hygiene.search.sidecar_days import days_of, undated_days

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.http import Response
    from media_hygiene.search.hand_index import HandIndex
    from media_hygiene.services.date_sidecars import DatesWritten, DateWriter

DATE_PATH: Final = "/api/date"
_MOST: Final = 20_000  # photos picked at once, as *Move to an event…*


class DateAsked(BaseModel):
    """What the page asks: days to propose, or one day given."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["propose", "set"] = "propose"
    keys: tuple[int, ...] = Field(min_length=1, max_length=_MOST)
    day: date | None = None


@dataclass(frozen=True, slots=True)
class DateDesk:
    """The days of the sidecars: the search, the writer, the files set aside."""

    index: HandIndex
    mapper: HostPathMapper
    writer: DateWriter
    aside: Callable[[], frozenset[str]]

    def read_again(self) -> None:
        """Read every sidecar's day again, for the search."""
        self.index.give_days(undated_days(self.index.connection))

    async def answer(self, body: bytes) -> Response:
        """Propose days, or write one into the sidecars of the photos picked.

        Args:
            body: `DateAsked`, as JSON.

        Returns:
            The days proposed, or the count read back and the undo line; 400 for a
            body that cannot be read, 409 with the reason when nothing can be written.
        """
        try:
            asked = DateAsked.model_validate_json(body)
        except ValidationError as exc:
            said = exc.errors()[0]["msg"] if exc.errors() else str(exc)
            return json_response(HTTPStatus.BAD_REQUEST, {"error": said})
        photos, own = self._undated(asked.keys)
        if asked.action == "propose" or asked.day is None:
            found = proposals(self.index.connection, photos)
            return json_response(HTTPStatus.OK, {"days": found})
        day = asked.day.isoformat()
        try:
            self.writer.ensure_ready()
            jobs = self.writer.jobs(photos, day)
            done = await asyncio.to_thread(self.writer.write, jobs)
        except MediaHygieneError as exc:
            said = " ".join(filter(None, (exc.message, exc.tip)))
            return json_response(HTTPStatus.CONFLICT, {"error": said})
        return json_response(HTTPStatus.OK, self._read_back(photos, day, (done, own)))

    def _undated(self, keys: tuple[int, ...]) -> tuple[tuple[Path, ...], int]:
        """The photos that can take a date: not set aside, without one of their own.

        Args:
            keys: The keys picked.

        Returns:
            Them, and how many were left for their own date.
        """
        found = [photo.path for key in keys if (photo := self.index.source_of(key))]
        kept = AsideFilter(self.aside, self.mapper).keep(found).files
        rows = self.index.connection.execute(
            "SELECT path, media_date FROM files WHERE path IN"
            " (SELECT value FROM json_each(?))",
            (json.dumps([str(path) for path in kept]),),
        )
        dated = {row[0] for row in rows if media_day(row[1])}
        photos = tuple(path for path in kept if str(path) not in dated)
        return photos, len(kept) - len(photos)

    def _read_back(
        self, photos: tuple[Path, ...], day: str, counted: tuple[DatesWritten, int]
    ) -> dict[str, object]:
        """Read the sidecars back, give the search their days, say what they hold.

        Args:
            photos: The photos asked.
            day: The day given.
            counted: The run, and the files left for their own date.

        Returns:
            `saved` (the line), `run`, `count`.
        """
        done, own = counted
        self.read_again()
        read = days_of(photos)
        count = sum(1 for photo in photos if read.get(photo) == day)
        said = ngettext(
            "{day} written beside {n} photo, read back from its sidecar.",
            "{day} written beside {n} photos, read back from their sidecars.",
            count,
        ).format(day=day, n=count)
        left = done.notes(own)
        if done.run:
            said += " " + done.undo_line()
        return {"saved": " ".join((said, *left)), "run": done.run, "count": count}
