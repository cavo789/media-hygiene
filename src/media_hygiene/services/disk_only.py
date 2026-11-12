"""`GET /disk-space/api/only?run=<run>`: a run's only copies, before *Purge* (0699).

The quarantine's page lists them above its *Purge* button, and its one question names
how many, before anything is erased: the console's `purge` does the same.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

from pydantic import BaseModel, ConfigDict

from media_hygiene.actions.runs import RUN_ID_PATTERN
from media_hygiene.console.formatting import human_size
from media_hygiene.review.http import ContentType, Response
from media_hygiene.services.only_copies import SHOWN, only_copies
from media_hygiene.services.quarantines import mounted_quarantines

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.services.runtime import Runtime


class OnlyShown(BaseModel):
    """The only copies of a run: how many, their size, the first ones by name."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    count: int
    size: str
    files: tuple[str, ...]  # as Windows names them, the first `SHOWN`


def only_shown(runtime: Runtime, run_id: str) -> OnlyShown:
    """Find, on the disk, the files of a run that exist nowhere else.

    Args:
        runtime: Settings and mount points.
        run_id: The run.

    Returns:
        What the page lists.
    """
    quarantines = mounted_quarantines(runtime).folders
    found = only_copies(quarantines, runtime.locations.journal_dir, (run_id,))
    files = tuple(runtime.mapper.to_host(file) for file in found.files[:SHOWN])
    return OnlyShown(count=len(found.files), size=human_size(found.size), files=files)


def only_answer(runtime: Runtime, request: Request) -> Response:
    """Answer `GET …/api/only?run=<run>`.

    Args:
        runtime: Settings and mount points.
        request: The request.

    Returns:
        JSON; 400 without a run identifier.
    """
    run_id = next(iter(parse_qs(request.query).get("run", ())), "")
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        return Response(HTTPStatus.BAD_REQUEST)
    body = only_shown(runtime, run_id).model_dump_json().encode()
    return Response(HTTPStatus.OK, body, ContentType.JSON)
