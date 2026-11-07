"""`POST /api/events/grouping`: the events as the values typed would make them (0643).

The page sends the three grouping values before saving them; the index's dated photos
are cut with the values `config.toml` holds and with those, and the differences come
back (`grouping_preview.compared`). Nothing is written. The trip distance is checked,
not previewed: trips need the home place and the towns of a classify run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.grouping_preview import Grouping, compared
from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response
from media_hygiene.review.setting_group import held
from media_hygiene.review.setting_groups import EVENTS
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.span_cards import when_taken

if TYPE_CHECKING:
    import sqlite3
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.review.http import Response

GROUPING_PATH: Final = "/api/events/grouping"
_DATED: Final = (
    f"SELECT {DAY}(media_date), media_date FROM files"  # noqa: S608
    f" WHERE {DAY}(media_date) IS NOT NULL"
)


@dataclass(frozen=True, slots=True)
class GroupingPreview:
    """The index and the file the kept values are read from."""

    connection: sqlite3.Connection
    config_file: Path
    session_hours: float  # `[classify] session_gap_hours`, not on the page

    def times(self) -> list[datetime]:
        """When each dated photo of the index was taken, oldest first.

        Returns:
            The times.
        """
        rows = self.connection.execute(_DATED).fetchall()
        return sorted(
            when_taken((0, "", 0, 0, day, written, None)) for day, written in rows
        )

    def grouping(self, values: dict[str, object]) -> Grouping:
        """The grouping of the three values of the page or of the file.

        Args:
            values: `merge_gap_hours`, `min_event_size` (checked).

        Returns:
            The grouping.

        Raises:
            TypeError: A value of another kind.
        """
        merge, size = values["merge_gap_hours"], values["min_event_size"]
        if not isinstance(merge, int | float) or not isinstance(size, int):
            raise TypeError(values)
        return Grouping(self.session_hours, float(merge), size)

    def answer(self, body: bytes) -> Response:
        """Compare the values kept with the values asked.

        Args:
            body: The three values, as the save would send them.

        Returns:
            `grouping_preview.compared`; 400 for values the save would refuse.
        """
        try:
            asked = json.loads(body)
            if not isinstance(asked, dict) or set(asked) != {
                one.key for one in EVENTS.fields
            }:
                raise ValueError  # noqa: TRY301
            if not all(one.accepts(asked[one.key]) for one in EVENTS.fields):
                raise ValueError  # noqa: TRY301
            now = self.grouping(held(self.config_file, EVENTS))
            tried = self.grouping(asked)
        except ValueError, TypeError:
            return json_response(HTTPStatus.BAD_REQUEST, {"error": _("Bad request.")})
        return json_response(HTTPStatus.OK, compared(self.times(), now, tried))
