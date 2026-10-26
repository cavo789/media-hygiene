"""*I checked: sort these N files* on the search page (0397): a group sorted, journaled.

The files the rule of a period would take (0396), checked on the page, are written as
file choices into `sort-decisions.json` of the latest classify run (each to the folder
the page showed it going to), read back from the disk, then `sort` runs cut to those
rows: the same guards (a persistent `/journal`, no `:ro` data mount), journal, manifest
and `undo` as `sort --event`. The plan and the workbook are read once (measured on the
maintainer's run of 52,056 rows: 1.1 s and 4.3 s). A file an earlier run of the plan
moved is recognised at its new place and counted as sorted; one the run does not know
(added since), or in a protected or `leave` folder, is left and counted; one the plan
leaves for another reason (a folder the user named) moves: the user picked it. Nothing
to move: no run at all.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_resume import moved_targets
from media_hygiene.classify.models import SortReason
from media_hygiene.classify.page_decisions import (
    FileDecision,
    PageDecisions,
    read_page_decisions,
    write_page_decisions,
)
from media_hygiene.classify.page_overlay import overlay
from media_hygiene.classify.page_values import FileValue
from media_hygiene.classify.workbook.reader import read_edits
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.group_sort_models import Counted, GroupSorted, Matched
from media_hygiene.services.page_choices import page_decisions, page_file
from media_hygiene.services.sort import SortService
from media_hygiene.services.sort_event import only_rows
from media_hygiene.services.sort_inputs import find_workbook, inputs_of, plan_of

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.classify.workbook.edits import Edits
    from media_hygiene.services.runtime import Runtime


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
    plan_file, plan = plan_of(runtime, workbook)
    found = _match(runtime, plan, folders)
    counted: Counted = {
        "unknown": found.unknown,
        "fixed": found.fixed,
        "already": found.already,
    }
    if not found.rows:
        return GroupSorted("", 0, 0, intact=True, **counted)
    edits = read_edits(workbook, plan)
    chosen = _choose((plan_file, plan, edits), found.rows, category)
    inputs = inputs_of(workbook, plan, overlay(edits, chosen))
    prepared = service.prepare(only_rows(inputs, frozenset(found.rows)))
    if not prepared.plan.groups:
        return GroupSorted("", 0, 0, intact=True, **counted)
    result = service.execute(prepared, lambda: False)
    done = result.manifest
    return GroupSorted(
        result.run_id,
        done.moved,
        done.verified,
        done.intact,
        **counted,
        links=(*result.links.lines, *result.links.problems),
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


def _match(
    runtime: Runtime, plan: ClassifyPlan, folders: Mapping[Path, str]
) -> Matched:
    """Find the plan's row of each file of the group, where it is now.

    Args:
        runtime: Mount points (host paths), the journal (rows moved since).
        plan: The latest classify plan.
        folders: Container path → its folder.

    Returns:
        The rows to move, and the files counted apart.
    """
    by_host = {row.path: row for row in plan.rows}
    moved = moved_targets(runtime.locations.journal_dir, plan.plan_id)
    now = {runtime.mapper.to_host(path): row for row, path in moved.items()}
    rows: dict[str, str] = {}
    already = fixed = 0
    for path, folder in folders.items():
        host = runtime.mapper.to_host(path)
        if host in now:
            already += 1
            continue
        row = by_host.get(host)
        if row is None:
            continue
        if row.reason is SortReason.LEFT_AS_IS:  # protected, `leave`: never moved
            fixed += 1
        else:
            rows[row.id] = folder
    unknown = len(folders) - len(rows) - already - fixed
    return Matched(rows, already, fixed, unknown)


def _choose(
    read: tuple[Path, ClassifyPlan, Edits], rows: Mapping[str, str], category: str
) -> PageDecisions:
    """Write the folder of each row as a file choice of the page, read it back.

    Args:
        read: The plan's file, the plan, the workbook's edits.
        rows: Row id → its folder.
        category: The rule's category.

    Returns:
        The page's choices, as the disk holds them.

    Raises:
        DecisionsError: The choices did not read back as written.
    """
    plan_file, plan, edits = read
    base = page_decisions(plan_file, plan)
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
    disk = read_page_decisions(target, plan.plan_id)
    held = {item.row: item for item in disk.files}
    if any(held.get(row) != decision for row, decision in decided.items()):
        raise DecisionsError(
            _("The choices did not read back as written: nothing moved.")
        )
    return disk
