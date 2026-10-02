"""Write what `classify` proposes: `plan.json`, `classify.xlsx` and the report.

Everything goes to `<reports>/<stamp>-classify/`, only when `/reports` is persistent:
a workbook edited in a folder the container forgets would be lost work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.carry import carry_over
from media_hygiene.classify.carry_plan import with_carried
from media_hygiene.classify.plan_build import build_plan
from media_hygiene.classify.workbook.prefill import Prefill
from media_hygiene.classify.workbook.writer import write_workbook
from media_hygiene.constants import (
    CLASSIFY_FOLDER_SUFFIX,
    CLASSIFY_PLAN_FILE_NAME,
    CLASSIFY_WORKBOOK_FILE_NAME,
)
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.report.classify_writer import ClassifyReportWriter
from media_hygiene.report.folders import new_report_folder
from media_hygiene.services.writable import writable_tip

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.carry_models import CarryRecord
    from media_hygiene.classify.carry_types import CarrySource
    from media_hygiene.services.classify import ClassifyResult
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class ClassifyOutput:
    """The folder written, and what was carried over from the previous workbook."""

    folder: Path
    carried: CarryRecord | None = None


def write_classify_output(
    runtime: Runtime, result: ClassifyResult, source: CarrySource | None = None
) -> ClassifyOutput | None:
    """Write the plan, the workbook and the report of a classify run.

    Args:
        runtime: Settings, mount points and output.
        result: The proposals.
        source: The previous workbook, whose edits are carried over.

    Returns:
        The folder written, or None when `/reports` would not survive the container.

    Raises:
        MountError: The folder could not be written; the proposals are on screen.
    """
    if not runtime.persistent(MountKind.REPORTS):
        return None
    reports_dir = runtime.locations.reports_dir
    plan = build_plan(result.classification, runtime.settings.classify, runtime.mapper)
    prefill = None
    if source is not None:
        carried = carry_over(source, plan)
        plan = with_carried(plan, carried, source)
        prefill = Prefill(carried.edits, carried.notes)
    try:
        folder = new_report_folder(reports_dir, CLASSIFY_FOLDER_SUFFIX)
        (folder / CLASSIFY_PLAN_FILE_NAME).write_text(
            plan.model_dump_json(indent=1), encoding="utf-8"
        )
        write_workbook(plan, folder / CLASSIFY_WORKBOOK_FILE_NAME, prefill)
        with runtime.executor_factory() as executor:
            ClassifyReportWriter(folder, runtime.mapper, executor).write(plan)
    except OSError as exc:
        raise MountError(
            _("The classify files could not be written to {folder}: {reason}.").format(
                folder=runtime.mapper.to_host(reports_dir),
                reason=exc.strerror or exc,
            ),
            writable_tip((reports_dir,)) if isinstance(exc, PermissionError) else None,
        ) from exc
    return ClassifyOutput(folder, plan.carried)
