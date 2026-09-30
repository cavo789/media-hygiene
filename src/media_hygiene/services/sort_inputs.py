"""Find what `sort` applies: the workbook, its `plan.json`, and the edits it holds.

The workbook may be a copy edited anywhere mounted; its plan is found under `/reports`
by the plan id its `_meta` sheet records. Without a workbook named, the latest classify
run is taken, as `undo` takes the latest run.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.classify.workbook.reader import read_edits, read_plan_id
from media_hygiene.constants import (
    CLASSIFY_FOLDER_SUFFIX,
    CLASSIFY_PLAN_FILE_NAME,
    CLASSIFY_WORKBOOK_FILE_NAME,
)
from media_hygiene.errors import MountError, WorkbookError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from media_hygiene.classify.workbook.edits import Edits
    from media_hygiene.services.runtime import Runtime

# Excel and LibreOffice keep these next to a workbook they have open.
_LOCK_FILES: Final = ("~${name}", ".~lock.{name}#")


@dataclass(frozen=True, slots=True)
class SortInputs:
    """The workbook, its plan, what the user changed, and when it was saved."""

    workbook: Path
    plan: ClassifyPlan
    edits: Edits
    saved_at: datetime
    open_elsewhere: bool  # Excel or LibreOffice still has it open

    @property
    def edit_count(self) -> int:
        """Count the cells the user filled.

        Returns:
            Files, events and categories edited.
        """
        edits = self.edits
        return len(edits.files) + len(edits.events) + len(edits.categories)


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
        runs = sorted(
            runtime.locations.reports_dir.glob(
                f"*-{CLASSIFY_FOLDER_SUFFIX}*/{CLASSIFY_WORKBOOK_FILE_NAME}"
            ),
            reverse=True,
        )
        if not runs:
            raise WorkbookError(
                _("No classify workbook in /reports."),
                _("Run 'classify' first, then edit its workbook."),
            )
        return runs[0]
    for candidate in (Path(given), runtime.mapper.to_container(given)):
        if candidate.is_file():
            return candidate
    raise WorkbookError(
        _("The workbook {path} was not found.").format(path=given),
        _("Give its path in a mounted folder, e.g. the one mounted on /reports."),
    )


def load_inputs(runtime: Runtime, workbook: Path) -> SortInputs:
    """Find the plan of a workbook, check the workbook against it, read the edits.

    Args:
        runtime: Settings, mount points and output.
        workbook: The workbook (container path).

    Returns:
        Everything `sort` applies.
    """
    plan = _plan_of(runtime, workbook)
    edits = read_edits(workbook, plan)
    locks = (pattern.format(name=workbook.name) for pattern in _LOCK_FILES)
    return SortInputs(
        workbook=workbook,
        plan=plan,
        edits=edits,
        saved_at=datetime.fromtimestamp(workbook.stat().st_mtime).astimezone(),
        open_elsewhere=any((workbook.parent / lock).exists() for lock in locks),
    )


def _plan_of(runtime: Runtime, workbook: Path) -> ClassifyPlan:
    """Find the `plan.json` a workbook belongs to: next to it, else under `/reports`.

    Args:
        runtime: Settings, mount points and output.
        workbook: The workbook.

    Returns:
        The plan whose id the workbook records.

    Raises:
        WorkbookError: No plan under `/reports` has that id.
    """
    plan_id = read_plan_id(workbook)
    beside = workbook.parent / CLASSIFY_PLAN_FILE_NAME
    others = sorted(
        runtime.locations.reports_dir.glob(f"*/{CLASSIFY_PLAN_FILE_NAME}"),
        reverse=True,
    )
    for candidate in (beside, *others):
        plan = _read_plan(candidate)
        if plan is not None and plan.plan_id == plan_id:
            return plan
    raise WorkbookError(
        _("The plan.json of this workbook ({plan_id}) is not in /reports.").format(
            plan_id=plan_id
        ),
        _(
            "Keep plan.json in the folder 'classify' wrote, or run 'classify' again "
            "and edit its new workbook."
        ),
    )


def _read_plan(path: Path) -> ClassifyPlan | None:
    """Read a `plan.json`.

    Args:
        path: The file.

    Returns:
        The plan, or None when it is missing or not a plan this version reads.
    """
    try:
        return ClassifyPlan.model_validate_json(path.read_text(encoding="utf-8"))
    except OSError, ValidationError:
        return None
