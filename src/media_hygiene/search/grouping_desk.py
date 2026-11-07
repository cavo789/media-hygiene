"""`POST /api/events/grouping`: the events and trips of the values typed (0643, 0646).

The page sends the three grouping values before saving them; the files `classify` works
on are cut with the values `config.toml` holds and with those, and the differences come
back (`grouping_preview.previewed`). Nothing is written.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response
from media_hygiene.review.setting_group import held
from media_hygiene.review.setting_groups import EVENTS

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from media_hygiene.review.http import Response

GROUPING_PATH: Final = "/api/events/grouping"


@dataclass(frozen=True, slots=True)
class GroupingPreview:
    """The file the kept values are read from, and how two sets of values compare."""

    config_file: Path
    look: Callable[[Mapping[str, object], Mapping[str, object]], dict[str, object]]

    def answer(self, body: bytes) -> Response:
        """Compare the values kept with the values asked.

        Args:
            body: The three values, as the save would send them.

        Returns:
            The comparison; 400 for values the save would refuse.
        """
        try:
            asked = json.loads(body)
        except ValueError:
            asked = None
        if (
            not isinstance(asked, dict)
            or set(asked) != {one.key for one in EVENTS.fields}
            or not all(one.accepts(asked[one.key]) for one in EVENTS.fields)
        ):
            return json_response(HTTPStatus.BAD_REQUEST, {"error": _("Bad request.")})
        now = held(self.config_file, EVENTS)
        return json_response(HTTPStatus.OK, self.look(now, asked))
