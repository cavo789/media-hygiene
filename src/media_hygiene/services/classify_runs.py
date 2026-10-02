"""The classify runs under `/reports`: their workbooks and their `plan.json` files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.constants import (
    CLASSIFY_FOLDER_SUFFIX,
    CLASSIFY_PLAN_FILE_NAME,
    CLASSIFY_WORKBOOK_FILE_NAME,
)

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def latest_workbook(runtime: Runtime) -> Path | None:
    """The workbook of the latest classify run.

    Args:
        runtime: Mount points.

    Returns:
        It, container path; None when no classify run wrote one.
    """
    runs = sorted(
        runtime.locations.reports_dir.glob(
            f"*-{CLASSIFY_FOLDER_SUFFIX}*/{CLASSIFY_WORKBOOK_FILE_NAME}"
        ),
        reverse=True,
    )
    return runs[0] if runs else None


def locate(runtime: Runtime, given: str) -> Path | None:
    """Find a workbook named by the user: a container path, else a host path.

    Args:
        runtime: Settings, mount points and output.
        given: The path typed.

    Returns:
        The file, container path; None when it is not there.
    """
    for candidate in (Path(given), runtime.mapper.to_container(given)):
        if candidate.is_file():
            return candidate
    return None


def find_plan(runtime: Runtime, workbook: Path, plan_id: str) -> ClassifyPlan | None:
    """Find a plan by its id: next to the workbook first, then under `/reports`.

    Args:
        runtime: Settings, mount points and output.
        workbook: The workbook.
        plan_id: The plan id; empty (its `_meta` is lost): the plan next to it.

    Returns:
        The plan, or None.
    """
    found = find_plan_file(runtime, workbook, plan_id)
    return None if found is None else found[1]


def find_plan_file(
    runtime: Runtime, workbook: Path, plan_id: str
) -> tuple[Path, ClassifyPlan] | None:
    """Find a plan and its `plan.json`, as `find_plan` does.

    Args:
        runtime: Settings, mount points and output.
        workbook: The workbook.
        plan_id: The plan id; empty: the plan next to it.

    Returns:
        Its file and the plan, or None.
    """
    beside = workbook.parent / CLASSIFY_PLAN_FILE_NAME
    if not plan_id:
        plan = _read_plan(beside)
        return None if plan is None else (beside, plan)
    others = sorted(
        runtime.locations.reports_dir.glob(f"*/{CLASSIFY_PLAN_FILE_NAME}"),
        reverse=True,
    )
    for candidate in (beside, *others):
        plan = _read_plan(candidate)
        if plan is not None and plan.plan_id == plan_id:
            return candidate, plan
    return None


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
