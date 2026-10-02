"""Find the workbook whose edits `classify` carries over, before anything is proposed.

By default, the workbook of the latest classify run: the one `sort` would apply.
`--carry-over <workbook>` names another one; `--no-carry-over` starts fresh. A workbook
that cannot be read stops `classify` before it writes a newer run: its edits would
otherwise be buried under a workbook without them.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_resume import moved_rows
from media_hygiene.classify.carry_models import LostEdit, LostWhy
from media_hygiene.classify.carry_types import CarrySource
from media_hygiene.classify.page_overlay import overlay
from media_hygiene.classify.workbook.salvage import salvage
from media_hygiene.console.formatting import human_number
from media_hygiene.errors import WorkbookError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.classify_runs import (
    find_plan_file,
    latest_workbook,
    locate,
)
from media_hygiene.services.page_choices import page_decisions

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.classify.workbook.salvage_models import Salvaged
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
    found = find_plan_file(runtime, path, salvaged.plan_id)
    plan = None if found is None else found[1]
    applied = frozenset[str]()
    if found is not None:
        salvaged = _with_page(runtime, found, salvaged)
        applied = moved_rows(runtime.locations.journal_dir, found[1].plan_id)
    saved = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    return CarrySource(
        workbook=host,
        saved_at=saved.isoformat(timespec="minutes"),
        salvaged=salvaged,
        plan=plan,
        applied=applied,
    )


def _with_page(
    runtime: Runtime, found: tuple[Path, ClassifyPlan], salvaged: Salvaged
) -> Salvaged:
    """Lay the choices of the review page over the salvaged edits.

    A choice the workbook contradicts since is not carried: the workbook's value is,
    and the page's is listed among the edits left behind.

    Args:
        runtime: Settings, mount points and output.
        found: The previous `plan.json` and its plan.
        salvaged: The edits of the previous workbook.

    Returns:
        The edits to carry over.
    """
    page = overlay(salvaged.edits, page_decisions(*found))
    if page.applied:
        runtime.output.info(
            _("Choices of the review page carried over too: {count}.").format(
                count=human_number(page.applied)
            )
        )
    left = (
        LostEdit(sheet=item.sheet, key=item.key, value=item.page, why=LostWhy.CONFLICT)
        for item in page.conflicts
    )
    return replace(salvaged, edits=page.edits, invalid=(*salvaged.invalid, *left))
