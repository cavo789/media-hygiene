"""`GET /disk-space/api/only?run=<run>`: a run's only copies, before *Purge* (0699).

The quarantine's page lists them above its *Purge* button, and its one question names
how many, before anything is erased: the console's `purge` does the same. The disk
space page counts them per run from the index (`only_by_run`, 0775): one query per run
instead of a stat per file through Docker Desktop; *Purge* asks the disk itself.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

from pydantic import BaseModel, ConfigDict

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.runs import RUN_ID_PATTERN
from media_hygiene.console.formatting import human_size
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.http import ContentType, Response
from media_hygiene.services.only_copies import SHOWN, only_copies
from media_hygiene.services.only_count import OnlyCount, only_count
from media_hygiene.services.quarantines import mounted_quarantines

if TYPE_CHECKING:
    from collections.abc import Sequence

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


def only_by_run(runtime: Runtime, runs: Sequence[str]) -> dict[str, int] | None:
    """Count, from the index, the files of each run that exist nowhere else.

    Args:
        runtime: Settings and mount points.
        runs: The runs in the quarantine.

    Returns:
        The count by run; a run whose journal is lost is left out (every one of its
        files counts then, as `purge` counts them). None without a readable index.
    """
    counted = counts_by_run(runtime, runs)
    return None if counted is None else {r: c.only for r, c in counted.items()}


def counts_by_run(runtime: Runtime, runs: Sequence[str]) -> dict[str, OnlyCount] | None:
    """Count, from the index, each run's files nowhere else and only on the NAS (0792).

    Args:
        runtime: Settings and mount points.
        runs: The runs in the quarantine.

    Returns:
        The counts by run, as `only_by_run` leaves runs out; None without a readable
        index.
    """
    if not runs or not runtime.persistent(MountKind.CACHE):
        return None
    journal_dir = runtime.locations.journal_dir
    counts: dict[str, OnlyCount] = {}
    for run in runs:
        if not journal_file(journal_dir, run).is_file():
            continue
        count = only_count(runtime.locations.index_file, journal_dir, (run,))
        if count is None:
            return None
        counts[run] = count
    return counts
