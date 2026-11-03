"""*Do not sort this event* and *Undo my choice* of the Events tab (0574).

`POST /api/events/left` with `{event: "<first>..<last>", left}`: the event's files not
sorted yet (as `span_events` lists them) are kept by content id in
`/config/events/left.toml`, or taken out of it. The answer is read back from the disk:
whether the event is left now, and the sentence to show. A file not hashed yet has no id
and cannot be kept: said in the answer.
"""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.classify.event_left import set_left
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.serving import json_response
from media_hygiene.search.span_cards import BETWEEN, ids_of

if TYPE_CHECKING:
    from media_hygiene.review.http import Response
    from media_hygiene.search.span_events import SpanEvents

LEFT_PATH: Final = "/api/events/left"
_LONGEST: Final = 64  # two ISO times and `..`


class LeftIn(BaseModel):
    """The event, and whether it stays where it is."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event: str = Field(min_length=3, max_length=_LONGEST)
    left: bool


def left_answer(span: SpanEvents | None, body: bytes) -> Response:
    """Keep an event where it is, or take that choice back, then read it back.

    Args:
        span: The Events tab made from the index; None: the page has none.
        body: `{event, left}`.

    Returns:
        `{left, said}`; 400 for a body or an event that cannot be read, 404 without a
        tab or a settings folder.
    """
    if span is None or span.config_dir is None:
        return json_response(HTTPStatus.NOT_FOUND, {"error": _("No Events tab here.")})
    try:
        asked = LeftIn.model_validate_json(body)
        first, _between, last = asked.event.partition(BETWEEN)
        rows = span.event_rows(
            datetime.fromisoformat(first), datetime.fromisoformat(last)
        )
    except (ValidationError, ValueError) as exc:
        return json_response(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
    ids = ids_of(rows)
    if not ids:
        said = _("Its files are not hashed yet: run an audit, then choose again.")
        return json_response(HTTPStatus.CONFLICT, {"error": said})
    try:
        held = set_left(span.config_dir, ids, left=asked.left)
    except ConfigError as exc:
        return json_response(HTTPStatus.CONFLICT, {"error": exc.message})
    left = ids <= held
    return json_response(HTTPStatus.OK, {"left": left, "said": _said(left, len(rows))})


def _said(left: bool, files: int) -> str:  # noqa: FBT001  # the state read back
    """The sentence of the choice read back.

    Args:
        left: Whether the event is left where it is now.
        files: Its files.

    Returns:
        It.
    """
    if left:
        said = ngettext(
            "Saved in events/left.toml, read back: this file stays where it is.",
            "Saved in events/left.toml, read back:"
            " these {n} files stay where they are.",
            files,
        )
    else:
        said = ngettext(
            "Choice taken back, read back: this file is to decide again.",
            "Choice taken back, read back: these {n} files are to decide again.",
            files,
        )
    return said.format(n=files)
