"""*I checked: sort these N files* on the search page (0397): a group sorted, journaled.

The files the rule of a period would take (0396), checked on the page, are written as
file choices into `sort-decisions.json` of the latest classify run (each to the folder
the page showed it going to), read back from the disk, then `sort` runs cut to those
rows: the same guards (a persistent `/journal`, no `:ro` data mount), journal, manifest
and `undo` as `sort --event`. A file the run does not know (added since) is left out
and counted, as is one the plan leaves as it is.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.models import Band
from media_hygiene.classify.page_decisions import (
    FileDecision,
    PageDecisions,
    read_page_decisions,
    write_page_decisions,
)
from media_hygiene.classify.page_values import FileValue
from media_hygiene.classify.workbook.reader import read_edits
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.page_choices import page_decisions, page_file
from media_hygiene.services.sort import SortService
from media_hygiene.services.sort_event import only_rows
from media_hygiene.services.sort_inputs import find_workbook, load_inputs, plan_of

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class GroupSorted:
    """What the run did, read back; the files it could not take, counted."""

    run_id: str  # empty: nothing to move
    moved: int
    verified: int  # moves checked at their new place after the run
    intact: bool
    unknown: int  # files the classify run does not know: run classify again
    fixed: int  # files the plan leaves as they are


def sort_group(
    runtime: Runtime, folders: Mapping[Path, str], category: str
) -> GroupSorted:
    """Choose a folder for each file of a group, then sort exactly those files.

    Args:
        runtime: Settings, mount points and output.
        folders: Container path → the folder below its root it goes to.
        category: The rule's category, shown again on the review-sort page.

    Returns:
        The run, read back.
    """
    service = SortService(runtime, NullProgress())
    service.ensure_ready()  # refused before anything is written: no `/journal`, `:ro`
    workbook = find_workbook(runtime, None)
    plan = plan_of(runtime, workbook)[1]
    rows = _rows(runtime, plan, folders)
    _choose(runtime, workbook, (rows, category))
    inputs = only_rows(load_inputs(runtime, workbook), frozenset(rows))
    prepared = service.prepare(inputs)
    fixed = _fixed(runtime, plan, folders)
    unknown = len(folders) - len(rows) - fixed
    if not prepared.plan.groups:
        return GroupSorted("", 0, 0, intact=True, unknown=unknown, fixed=fixed)
    result = service.execute(prepared, lambda: False)
    done = result.manifest
    return GroupSorted(
        result.run_id,
        done.moved,
        done.verified,
        intact=done.intact,
        unknown=unknown,
        fixed=fixed,
    )


def _choose(
    runtime: Runtime, workbook: Path, chosen: tuple[Mapping[str, str], str]
) -> None:
    """Write the folder of each row as a file choice of the page, read it back.

    Args:
        runtime: Mount points.
        workbook: The latest classify workbook.
        chosen: Row id → its folder, and the rule's category.

    Raises:
        DecisionsError: The choices did not read back as written.
    """
    rows, category = chosen
    plan_file, plan = plan_of(runtime, workbook)
    base = page_decisions(plan_file, plan)
    edits = read_edits(workbook, plan)
    decided = {
        row: FileDecision(
            row=row,
            value=FileValue(folder=folder),
            base=FileValue.of(edits.files.get(row)),
            category=category,
        )
        for row, folder in rows.items()
    }
    kept = tuple(item for item in base.files if item.row not in decided)
    target = page_file(plan_file)
    written = PageDecisions(
        plan_id=plan.plan_id, events=base.events, files=(*kept, *decided.values())
    )
    write_page_decisions(target, written)
    disk = {item.row: item for item in read_page_decisions(target, plan.plan_id).files}
    if any(disk.get(row) != decision for row, decision in decided.items()):
        raise DecisionsError(
            _("The choices did not read back as written: nothing moved.")
        )


def sorted_group(
    runtime: Runtime, folders: Mapping[Path, str], category: str
) -> dict[str, object]:
    """`sort_group` for the page: the run read back, as JSON.

    Args:
        runtime: Settings, mount points and output.
        folders: Container path → its folder below its root.
        category: The rule's category.

    Returns:
        The run's fields.
    """
    return asdict(sort_group(runtime, folders, category))


def _rows(
    runtime: Runtime, plan: ClassifyPlan, folders: Mapping[Path, str]
) -> dict[str, str]:
    """The rows of the plan for the files of the group that may move.

    Args:
        runtime: Mount points: container paths ↔ host paths.
        plan: The latest classify plan.
        folders: Container path → its folder.

    Returns:
        Row id → its folder.
    """
    by_host = {row.path: row for row in plan.rows}
    found: dict[str, str] = {}
    for path, folder in folders.items():
        row = by_host.get(runtime.mapper.to_host(path))
        if row is not None and row.values is not None and row.band is not Band.STAY:
            found[row.id] = folder
    return found


def _fixed(runtime: Runtime, plan: ClassifyPlan, folders: Mapping[Path, str]) -> int:
    """How many files of the group the plan leaves as they are.

    Args:
        runtime: Mount points.
        plan: The latest classify plan.
        folders: The group.

    Returns:
        Their count.
    """
    hosts = {runtime.mapper.to_host(path) for path in folders}
    return sum(
        1
        for row in plan.rows
        if row.path in hosts and (row.values is None or row.band is Band.STAY)
    )
