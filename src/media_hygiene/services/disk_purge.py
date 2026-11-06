"""*Purge* from the disk space page: its files shown first, read back after (0616).

The button lives on the quarantine's page, on the tiles of the run. It sends how many
files it showed: a run that changed since is refused, and so is a run shown as nothing.
`mh` runs `purge <run> --yes` beside the server, the page having asked. Afterwards the
state tells what the disk says: the run gone or not, the room freed against the room
stated.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.console.formatting import human_size
from media_hygiene.i18n import _
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.step_watch import keep_step, keeps_server
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.services.quarantine_pick import quarantine_state
from media_hygiene.services.status import read_status

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.services.runtime import Runtime


class PurgeAsked(BaseModel):
    """`POST …/api/purge`: the run, and how many of its files the page showed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    files: int = Field(ge=1)


class PurgeReadBack(BaseModel):
    """The last purge asked from the page, as the disk says it now."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    gone: bool
    stated: str
    freed: str


@dataclass(frozen=True, slots=True)
class PurgeAsking:
    """What the disk said when the purge was asked."""

    run_id: str
    stated: int  # the run's bytes, as the page states them
    before: int  # the whole quarantine's


def read_back(runtime: Runtime, asking: PurgeAsking) -> PurgeReadBack:
    """Compare the quarantine now with what it was when the purge was asked.

    Args:
        runtime: Settings and mount points.
        asking: The purge asked.

    Returns:
        Whether the run is gone, the room stated and the room freed.
    """
    quarantine = read_status(runtime).quarantine
    return PurgeReadBack(
        run_id=asking.run_id,
        gone=all(run.run_id != asking.run_id for run in quarantine.runs),
        stated=human_size(asking.stated),
        freed=human_size(max(asking.before - quarantine.size, 0)),
    )


def _checked(runtime: Runtime, asked: PurgeAsked) -> PurgeAsking | None:
    """Check that the files shown are the run's files now.

    Args:
        runtime: Settings, mount points and output.
        asked: The run and the count shown.

    Returns:
        What the disk says, or None when the page showed something else.
    """
    shown = sum(tile.run == asked.run_id for tile in quarantine_state(runtime).tiles)
    quarantine = read_status(runtime).quarantine
    run = next((each for each in quarantine.runs if each.run_id == asked.run_id), None)
    if run is None or shown != asked.files:
        return None
    return PurgeAsking(asked.run_id, run.size, quarantine.size)


async def purge_response(
    runtime: Runtime, request: Request
) -> tuple[Response, PurgeAsking | None]:
    """Hand `purge <run> --yes` to `mh`, the files having been shown.

    Args:
        runtime: Settings, mount points and output.
        request: `POST …/api/purge`.

    Returns:
        The step to follow and what to read back after it; 400 on a bad body, 409
        when `mh` cannot run it or the run is not what the page showed.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused, None
    try:
        asked = PurgeAsked.model_validate_json(request.body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST), None
    if not keeps_server():
        message = _("This mh does not run the steps of the page: type the command.")
        return json_response(HTTPStatus.CONFLICT, {"error": message}), None
    asking = _checked(runtime, asked)
    if asking is None:
        message = _("This run changed since its files were shown: look at them again.")
        return json_response(HTTPStatus.CONFLICT, {"error": message}), None
    words = ("purge", asked.run_id, "--yes")
    answer = await keep_step(
        runtime.locations.reports_dir, words, " ".join((LAUNCHER_FUNCTION, *words))
    )
    return answer, asking if answer.status == HTTPStatus.OK else None
