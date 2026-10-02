"""Find what `sort` applies: the workbook, its `plan.json`, and the edits it holds.

The workbook may be a copy edited anywhere mounted; its plan is found under `/reports`
by the plan id its `_meta` sheet records. Without a workbook named, the latest classify
run is taken, as `undo` takes the latest run.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.page_overlay import overlay
from media_hygiene.classify.workbook.reader import read_edits, read_plan_id
from media_hygiene.errors import MountError, WorkbookError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.classify_runs import (
    find_plan_file,
    latest_workbook,
    locate,
)
from media_hygiene.services.page_choices import conflict_error, page_decisions

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.page_overlay import Overlaid
    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.classify.workbook.edits import Edits
    from media_hygiene.services.runtime import Runtime

# Excel and LibreOffice keep these next to a workbook they have open.
_LOCK_FILES: Final = ("~${name}", ".~lock.{name}#")


@dataclass(frozen=True, slots=True)
class SortInputs:
    """The workbook, its plan, what the user changed, and when it was saved.

    `edits` hold the workbook's edits with the choices of the review page laid over
    them (`page`).
    """

    workbook: Path
    plan: ClassifyPlan
    page: Overlaid
    saved_at: datetime
    open_elsewhere: bool  # Excel or LibreOffice still has it open

    @property
    def edits(self) -> Edits:
        """What the user changed, in the workbook and in the review page.

        Returns:
            The edits `sort` applies.
        """
        return self.page.edits

    @property
    def edit_count(self) -> int:
        """Count the cells the user filled in the workbook.

        Returns:
            Files, events and categories edited there.
        """
        edits, page = self.edits, self.page
        total = len(edits.files) + len(edits.events) + len(edits.categories)
        return total - page.applied + page.replaced


def find_workbook(runtime: Runtime, given: str | None) -> Path:
    """Resolve the workbook to apply: the one named, or the latest classify run's.

    Args:
        runtime: Settings, mount points and output.
        given: A host or container path, or None.

    Returns:
        The workbook, container path.

    Raises:
        MountError: `/reports` is not mounted: the plans live there.
        WorkbookError: No workbook there, or none at the path given.
    """
    if not runtime.persistent(MountKind.REPORTS):
        raise MountError(
            _("No reports mount: 'sort' reads the plan 'classify' wrote there."),
            _('Mount the same reports folder as for classify: -v "<folder>:/reports".'),
        )
    if given is None:
        latest = latest_workbook(runtime)
        if latest is None:
            raise WorkbookError(
                _("No classify workbook in /reports."),
                _("Run 'classify' first, then edit its workbook."),
            )
        return latest
    found = locate(runtime, given)
    if found is not None:
        return found
    raise WorkbookError(
        _("The workbook {path} was not found.").format(path=given),
        _("Give its path in a mounted folder, e.g. the one mounted on /reports."),
    )


def load_inputs(runtime: Runtime, workbook: Path) -> SortInputs:
    """Find the plan of a workbook, check the workbook against it, read the edits.

    The choices of the review page are laid over the workbook's edits.

    Args:
        runtime: Settings, mount points and output.
        workbook: The workbook (container path).

    Returns:
        Everything `sort` applies.

    Raises:
        WorkbookError: The page and the workbook disagree on an event or a file.
    """
    plan_file, plan = plan_of(runtime, workbook)
    page = overlay(read_edits(workbook, plan), page_decisions(plan_file, plan))
    if page.conflicts:
        raise conflict_error(plan, page.conflicts)
    return SortInputs(
        workbook=workbook,
        plan=plan,
        page=page,
        saved_at=datetime.fromtimestamp(workbook.stat().st_mtime).astimezone(),
        open_elsewhere=open_elsewhere(workbook),
    )


def open_elsewhere(workbook: Path) -> bool:
    """Tell whether Excel or LibreOffice has the workbook open.

    Args:
        workbook: The workbook.

    Returns:
        True when their lock file lies next to it.
    """
    locks = (pattern.format(name=workbook.name) for pattern in _LOCK_FILES)
    return any((workbook.parent / lock).exists() for lock in locks)


def plan_of(runtime: Runtime, workbook: Path) -> tuple[Path, ClassifyPlan]:
    """Find the `plan.json` a workbook belongs to: next to it, else under `/reports`.

    Args:
        runtime: Settings, mount points and output.
        workbook: The workbook.

    Returns:
        The `plan.json` whose id the workbook records, and its plan.

    Raises:
        WorkbookError: No plan under `/reports` has that id.
    """
    plan_id = read_plan_id(workbook)
    found = find_plan_file(runtime, workbook, plan_id)
    if found is not None:
        return found
    raise WorkbookError(
        _("The plan.json of this workbook ({plan_id}) is not in /reports.").format(
            plan_id=plan_id
        ),
        _(
            "Keep plan.json in the folder 'classify' wrote, or run 'classify "
            "--carry-over <workbook>': your edits are carried over to its new workbook."
        ),
    )
