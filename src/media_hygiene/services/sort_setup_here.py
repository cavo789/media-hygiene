"""What the sort setup of the pages needs from a run: the latest plan (0533)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ValidationError

from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.constants import CLASSIFY_PLAN_FILE_NAME
from media_hygiene.search.sort_folder_desk import SortFolderDesk, SortSetup
from media_hygiene.search.sort_setup_desk import SortSetupDesk
from media_hygiene.services.classify_runs import latest_workbook

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.search.folder_role_desk import RoleDesk
    from media_hygiene.services.runtime import Runtime


def latest_plan(runtime: Runtime) -> ClassifyPlan | None:
    """The plan of the latest classify run, read each time: it may have been run since.

    Args:
        runtime: Mount points.

    Returns:
        It; None without a run, or with a plan this version does not read.
    """
    workbook = latest_workbook(runtime)
    if workbook is None:
        return None
    path = workbook.with_name(CLASSIFY_PLAN_FILE_NAME)
    try:
        return ClassifyPlan.model_validate_json(path.read_text(encoding="utf-8"))
    except OSError, ValidationError:
        return None


def sort_setup(
    runtime: Runtime, roles: RoleDesk, connection: sqlite3.Connection
) -> SortSetup:
    """The desks of the sort setup.

    Args:
        runtime: Mount points.
        roles: `config.toml`, the host paths, the mounted folders.
        connection: The search's index.

    Returns:
        Them.
    """
    setup = SortSetupDesk(roles, connection, lambda: latest_plan(runtime))
    return SortSetup(setup, SortFolderDesk(roles))
