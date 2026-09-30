"""Write what `classify` proposes: `plan.json`, `classify.xlsx` and the report.

Everything goes to `<reports>/<stamp>-classify/`, only when `/reports` is persistent:
a workbook edited in a folder the container forgets would be lost work.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.plan_build import build_plan
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
from media_hygiene.services.writable import writable_tip

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.classify import ClassifyResult
    from media_hygiene.services.runtime import Runtime

_STAMP_FORMAT: Final = "%Y%m%d-%H%M%S"


def write_classify_output(runtime: Runtime, result: ClassifyResult) -> Path | None:
    """Write the plan, the workbook and the report of a classify run.

    Args:
        runtime: Settings, mount points and output.
        result: The proposals.

    Returns:
        The folder written, or None when `/reports` would not survive the container.

    Raises:
        MountError: The folder could not be written; the proposals are on screen.
    """
    if not runtime.persistent(MountKind.REPORTS):
        return None
    reports_dir = runtime.locations.reports_dir
    plan = build_plan(result.classification, runtime.settings.classify, runtime.mapper)
    try:
        folder = _new_folder(reports_dir)
        (folder / CLASSIFY_PLAN_FILE_NAME).write_text(
            plan.model_dump_json(indent=1), encoding="utf-8"
        )
        write_workbook(plan, folder / CLASSIFY_WORKBOOK_FILE_NAME)
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
    return folder


def _new_folder(reports_dir: Path) -> Path:
    """Create `<stamp>-classify`, with a suffix when two runs share a second.

    Args:
        reports_dir: The reports mount point.

    Returns:
        The new, empty folder.
    """
    base = f"{datetime.now(UTC).strftime(_STAMP_FORMAT)}-{CLASSIFY_FOLDER_SUFFIX}"
    folder, suffix = reports_dir / base, 1
    while folder.exists():
        suffix += 1
        folder = reports_dir / f"{base}-{suffix}"
    folder.mkdir(parents=True)
    return folder
