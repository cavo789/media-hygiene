"""The plan the search's *🗂 Events* view walks through, event by event (0438).

The view reads the same workbook `sort` would apply (the latest classify run's by
default) and its plan; its choices go to `sort-decisions.json` next to `plan.json`,
never into the workbook: Excel may have it open. `sort` lays them over the workbook's
edits (`classify/page_overlay`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.page_overlay import overlay
from media_hygiene.classify.workbook.reader import read_edits
from media_hygiene.console.formatting import human_number
from media_hygiene.errors import MountError
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mounts import is_writable
from media_hygiene.review.sort_batch import SortBatchSession
from media_hygiene.review.sort_files import RuleBook, SortSource
from media_hygiene.services.page_choices import page_decisions, page_file
from media_hygiene.services.sort_inputs import find_workbook, open_elsewhere, plan_of
from media_hygiene.services.writable import writable_tip

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def open_sort_review(runtime: Runtime, given: str | None) -> SortBatchSession:
    """Read the workbook, its plan and the page's earlier choices.

    Args:
        runtime: Settings, mount points and output.
        given: The workbook named (host or container path), or None for the latest.

    Returns:
        The session.

    Raises:
        MountError: The choices could not be saved next to `plan.json`.
    """
    workbook = find_workbook(runtime, given)
    plan_file, plan = plan_of(runtime, workbook)
    if not is_writable(plan_file.parent):
        folder = runtime.mapper.to_host(plan_file.parent)
        raise MountError(
            _("The container cannot write to {folders}.").format(folders=folder),
            writable_tip([plan_file.parent]),
        )
    edits = read_edits(workbook, plan)
    base = page_decisions(plan_file, plan)
    target = page_file(plan_file)
    output, host = runtime.output, runtime.mapper.to_host
    if open_elsewhere(workbook):
        output.warning(
            _(
                "The workbook is open in Excel or LibreOffice: what is not saved is "
                "not shown."
            )
        )
    conflicts = overlay(edits, base).conflicts
    if conflicts:
        message = ngettext(
            "{count} earlier choice of the page was edited otherwise in the workbook "
            "since: shown in red, choose again.",
            "{count} earlier choices of the page were edited otherwise in the "
            "workbook since: shown in red, choose again.",
            len(conflicts),
        )
        output.warning(message.format(count=human_number(len(conflicts))))
    source = SortSource(
        plan,
        edits,
        target,
        (host(workbook), host(target)),
        runtime.mapper,
        runtime.locations.journal_dir,
        RuleBook(runtime.locations.config_file, runtime.settings.classify.rules),
    )
    return SortBatchSession(source, base)
