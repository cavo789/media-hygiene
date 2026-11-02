"""The Events view's choices of photos leave out the files set aside (0518).

A file set aside is a soft delete: sent to another category from the Events view,
it is dropped server-side, whatever the page picked (Ctrl+A, Shift, the rectangle).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.review.sort_batch import SortBatchSession
    from media_hygiene.search.events_desk import EventsDesk


def rows_kept(desk: EventsDesk, session: SortBatchSession, body: bytes) -> bytes:
    """The body of `POST /api/sort/files`, its rows set aside left out.

    Args:
        desk: The Events view: the files set aside, read now, and the mapper.
        session: The plan's session: the file of each row.
        body: The JSON the page sent.

    Returns:
        The body to apply; unchanged when it is not a JSON object with rows.
    """
    try:
        asked = json.loads(body)
    except ValueError:
        return body
    rows = asked.get("rows") if isinstance(asked, dict) else None
    if not isinstance(rows, list):
        return body
    aside = desk.chosen()
    if not aside:
        return body
    kept = [
        row
        for row in rows
        if not isinstance(row, str)
        or (path := session.preview_source(row)) is None
        or desk.mapper.to_host(path) not in aside
    ]
    return json.dumps({**asked, "rows": kept}).encode()
