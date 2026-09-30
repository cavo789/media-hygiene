"""Find the workbook whose edits `classify` carries over, before anything is proposed.

By default, the workbook of the latest classify run: the one `sort` would apply.
`--carry-over <workbook>` names another one; `--no-carry-over` starts fresh. A workbook
that cannot be read stops `classify` before it writes a newer run: its edits would
otherwise be buried under a workbook without them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_resume import moved_rows
from media_hygiene.classify.carry_types import CarrySource
from media_hygiene.classify.workbook.salvage import salvage
from media_hygiene.errors import WorkbookError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.classify_runs import find_plan, latest_workbook, locate

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class CarryRequest:
    """`--carry-over` and `--no-carry-over`."""

    workbook: str | None = None  # a host or container path; None: the latest
    enabled: bool = True


def carry_source(runtime: Runtime, request: CarryRequest) -> CarrySource | None:
    """Read the workbook whose edits are carried over.

    Args:
        runtime: Settings, mount points and output.
        request: The options given.

    Returns:
        What it holds; None when carrying is off, `/reports` is not mounted, or there
        is no previous workbook.

    Raises:
        WorkbookError: The workbook named is not there, or a workbook cannot be read.
    """
    if not request.enabled or not runtime.persistent(MountKind.REPORTS):
        return None
    if request.workbook is None:
        path = latest_workbook(runtime)
        if path is None:
            return None
    else:
        path = locate(runtime, request.workbook)
        if path is None:
            tip = _(
                "Give its path in a mounted folder, e.g. the one mounted on /reports."
            )
            message = _("The workbook {path} was not found.")
            raise WorkbookError(message.format(path=request.workbook), tip)
    return _read(runtime, path)


def _read(runtime: Runtime, path: Path) -> CarrySource:
    """Salvage a workbook, find its plan and the rows a sort already moved.

    Args:
        runtime: Settings, mount points and output.
        path: The workbook, container path.

    Returns:
        The source of the edits.

    Raises:
        WorkbookError: It cannot be read at all.
    """
    host = runtime.mapper.to_host(path)
    try:
        salvaged = salvage(path)
    except WorkbookError as exc:
        raise WorkbookError(
            exc.message,
            _(
                "Its edits would not be carried over: repair {path}, name another "
                "one with --carry-over, or start fresh with --no-carry-over."
            ).format(path=host),
        ) from exc
    plan = find_plan(runtime, path, salvaged.plan_id)
    applied = (
        moved_rows(runtime.locations.journal_dir, plan.plan_id)
        if plan is not None
        else frozenset()
    )
    saved = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    return CarrySource(
        workbook=host,
        saved_at=saved.isoformat(timespec="minutes"),
        salvaged=salvaged,
        plan=plan,
        applied=applied,
    )
