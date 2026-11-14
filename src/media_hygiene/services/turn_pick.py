"""The *Photos to straighten* page's data (0810): its tiles, *Turn*, *Never turn*.

The tiles are the turns `TurnService` would write now (proposed, but refused, in a
protected folder or a backup, or not a JPEG): what the page shows is what *Apply now*
turns. *Turn these* writes the photos picked under one journaled run; *Never turn*
keeps their refusal in the index (by path, any version: never proposed again), both
read back from the disk before the page says so.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.faces.straighten import ORIENTATION_OF
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.turn_refusals import TurnRefusals
from media_hygiene.review.near_views import folder_and_name
from media_hygiene.review.views import ORIGINAL_LINK, PREVIEW_LINK
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.repair_pick import tile_key
from media_hygiene.services.turn_apply import TurnService

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.actions.turn_write import TurnJob
    from media_hygiene.services.runtime import Runtime

_FROZEN: Final = ConfigDict(frozen=True, extra="forbid")
_DEGREES_OF: Final = {code: int(turn) for turn, code in ORIENTATION_OF.items()}


class TurnTile(BaseModel):
    """One photo to straighten, as the page shows it."""

    model_config = _FROZEN

    key: str
    name: str
    folder: str  # as Windows names it
    turn: int  # degrees clockwise
    preview: str
    original: str


class TurnState(BaseModel):
    """`GET /api/state`: every photo a turn would be written for now."""

    model_config = _FROZEN

    tiles: tuple[TurnTile, ...]


class TurnDone(BaseModel):
    """What *Turn these* or *Never turn* did, read back, and the page again."""

    model_config = _FROZEN

    done: int  # photos turned, or refusals read back
    left: tuple[str, ...]  # "<path>: <reason>"
    run_id: str | None  # the run to undo; None: nothing written
    state: TurnState


def turn_jobs_now(runtime: Runtime) -> tuple[TurnJob, ...]:
    """The turns *Apply now* would write now.

    Args:
        runtime: Settings and mount points.

    Returns:
        The jobs, by path.
    """
    return TurnService(runtime, NullProgress()).prepare()


def _tile(runtime: Runtime, job: TurnJob) -> TurnTile:
    key = tile_key(str(job.path))
    folder, name = folder_and_name(str(runtime.mapper.to_host(job.path)))
    return TurnTile(
        key=key,
        name=name,
        folder=folder,
        turn=_DEGREES_OF[job.code],
        preview=f"{PREVIEW_LINK}{key}.jpg",
        original=f"{ORIGINAL_LINK}{key}{job.path.suffix.lower()}",
    )


def turn_state(runtime: Runtime) -> TurnState:
    """Every photo a turn would be written for now.

    Args:
        runtime: Settings and mount points.

    Returns:
        Its tiles.
    """
    return TurnState(tiles=tuple(_tile(runtime, job) for job in turn_jobs_now(runtime)))


def _picked(runtime: Runtime, keys: Iterable[str]) -> tuple[TurnJob, ...]:
    wanted = set(keys)
    return tuple(
        job for job in turn_jobs_now(runtime) if tile_key(str(job.path)) in wanted
    )


def turn_source(runtime: Runtime, key: str) -> Path | None:
    """The photo a tile shows.

    Args:
        runtime: Settings and mount points.
        key: The tile's key.

    Returns:
        The file, or None for an unknown key.
    """
    found = _picked(runtime, (key,))
    return found[0].path if found else None


def turn_picked(runtime: Runtime, keys: Iterable[str]) -> TurnDone:
    """Turn the photos picked, journaled, each read back.

    Args:
        runtime: Settings, mount points and output.
        keys: The tiles picked; an unknown key (refused meanwhile) is ignored.

    Returns:
        What was turned, what was not and why, the run, the page again.

    Raises:
        MountError: No persistent journal, or read-only photo folders; nothing written.
    """
    jobs = _picked(runtime, keys)
    if not jobs:
        return TurnDone(done=0, left=(), run_id=None, state=turn_state(runtime))
    result = TurnService(runtime, NullProgress()).execute(jobs, lambda: False)
    host = runtime.mapper.to_host
    outcome = result.outcome
    left = tuple(
        f"{host(incident.path)}: {incident.reason}"
        for incident in (*outcome.skipped, *outcome.failed)
    )
    return TurnDone(
        done=outcome.done, left=left, run_id=result.run_id, state=turn_state(runtime)
    )


def refuse_picked(runtime: Runtime, keys: Iterable[str]) -> TurnDone:
    """Never turn the photos picked: their refusal kept in the index, read back.

    Args:
        runtime: Settings and mount points.
        keys: The tiles picked.

    Returns:
        How many refusals the index holds now of those, and the page again.
    """
    paths = {job.path for job in _picked(runtime, keys)}
    with FactsRepository.open(runtime.locations.index_file) as repository:
        refusals = TurnRefusals(repository.connection)
        refusals.refuse(paths)
        kept = len(paths & refusals.refused())
    return TurnDone(done=kept, left=(), run_id=None, state=turn_state(runtime))
