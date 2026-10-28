"""Files the latest classify plan does not know, given rows of their own (0452).

Photos imported after the latest `classify` run (a phone, a folder) are in the index
but not in `plan.json`: *Move to an event…* left them, "not in the latest classify
run". They go through the classify engine with the rules of `config.toml`, as a rule
tried on the search page does (`rule_trial`): their root, date and stable id are the
engine's, their folder the one the page chose. The rows live for this move only:
`plan.json` and its workbook are checked against each other cell by cell, so neither
changes. The journal keeps each move, so `undo` puts it back and a second move knows
the file at its new place. A row's event is left empty.
"""

from __future__ import annotations

from contextlib import closing
from typing import TYPE_CHECKING

from media_hygiene.classify.engine import classify
from media_hygiene.classify.plan_build import rows_of
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.services.classify_people import with_people
from media_hygiene.services.classify_scope import run_scope
from media_hygiene.services.rule_trial import index_inputs

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow
    from media_hygiene.services.runtime import Runtime


def with_newcomers(
    runtime: Runtime, plan: ClassifyPlan, folders: Mapping[Path, str]
) -> ClassifyPlan:
    """The plan with a row for each file it does not know, going to its folder.

    Args:
        runtime: Settings, mount points.
        plan: The latest plan.
        folders: Container path → the folder below its root, for the files the plan
            has no row for.

    Returns:
        The plan and those rows, in memory; the same plan when none is a media file
        the index knows.
    """
    files = _inputs(runtime, folders)
    if not files:
        return plan
    scope = with_people(run_scope(runtime, None), runtime)
    found = classify(files, runtime.settings.classify, scope)
    proposals = sorted(found.proposals, key=lambda p: str(p.file.path))
    chosen = {runtime.mapper.to_host(path): folder for path, folder in folders.items()}
    taken = {row.id for row in plan.rows}
    rows: list[PlanRow] = []
    for row in rows_of(proposals, runtime.mapper):
        row_id, more = row.id, 1
        while row_id in taken:  # a copy of a file of the plan: the same content
            more += 1
            row_id = f"{row.id}-{more}"
        taken.add(row_id)
        update = {"id": row_id, "event_id": "", "folder": chosen.get(row.path)}
        rows.append(row.model_copy(update=update))
    return plan.model_copy(update={"rows": (*plan.rows, *rows)})


def _inputs(runtime: Runtime, folders: Mapping[Path, str]) -> tuple[MediaInput, ...]:
    """What the engine needs of the files, from the index.

    Args:
        runtime: Settings, mount points.
        folders: The files, by container path.

    Returns:
        One input per media file the index knows; none without an index.
    """
    index = runtime.index_file
    versions = tuple(
        PhotoVersion(path, stat.st_size, stat.st_mtime_ns)
        for path in folders
        if path.is_file() and (stat := path.stat())
    )
    if index is None or not index.is_file() or not versions:
        return ()
    with closing(connect_read_only(index)) as connection:
        return index_inputs(runtime, connection, versions)
