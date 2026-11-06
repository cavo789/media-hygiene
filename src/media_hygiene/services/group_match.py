"""A group of files matched against the latest classify plan (0397, 0452).

Each file is found by its host path in the plan, or at the place an earlier run of the
plan moved it (the journal): there already in the folder asked, it is counted; moved
elsewhere, or below another root than the target chosen (0596), it moves again from that
place, as a file the plan does not know. A file
the plan does not know gets a row of its own for this move (`plan_newcomers`): the
plan then holds it, in memory only.
"""

from __future__ import annotations

from pathlib import PureWindowsPath
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_resume import moved_targets
from media_hygiene.classify.models import SortReason
from media_hygiene.services.group_sort_models import Matched
from media_hygiene.services.plan_newcomers import with_newcomers

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.services.group_sort_models import GroupMove
    from media_hygiene.services.runtime import Runtime


def match_group(
    runtime: Runtime, plan: ClassifyPlan, group: GroupMove
) -> tuple[ClassifyPlan, Matched]:
    """Match a group against the plan, given rows for the files it does not know.

    Args:
        runtime: Settings, mount points, the journal.
        plan: The latest classify plan.
        group: Container path → its folder, the root imposed if any.

    Returns:
        The plan with those rows (in memory), and the group matched against it.
    """
    found = _match(runtime, plan, group)
    if not found.strangers:
        return plan, found
    strangers = {path: group.folders[path] for path in found.strangers}
    whole = with_newcomers(runtime, plan, strangers)
    return whole, _match(runtime, whole, group) if whole is not plan else found


def _match(runtime: Runtime, plan: ClassifyPlan, group: GroupMove) -> Matched:
    """Find the plan's row of each file of the group, where it is now.

    Args:
        runtime: Mount points (host paths), the journal (rows moved since).
        plan: The latest classify plan.
        group: Container path → its folder, the root imposed if any.

    Returns:
        The rows to move, and the files counted apart.
    """
    by_host = {row.path: row for row in plan.rows}
    moved = moved_targets(runtime.locations.journal_dir, plan.plan_id)
    now = {runtime.mapper.to_host(path): row for row, path in moved.items()}
    rows: dict[str, str] = {}
    strangers: list[Path] = []
    already = fixed = 0
    root = runtime.mapper.to_host(group.root) if group.root else None
    for path, folder in group.folders.items():
        host = runtime.mapper.to_host(path)
        row = by_host.get(host)
        if row is None and host in now and _sits_in(host, folder, root):
            already += 1
            continue
        if row is None:  # unknown, or moved by an earlier run elsewhere: from here
            strangers.append(path)
            continue
        if row.reason is SortReason.LEFT_AS_IS:  # protected, `leave`: never moved
            fixed += 1
        else:
            rows[row.id] = folder
    return Matched(rows, already, fixed, tuple(strangers))


def _sits_in(host: str, folder: str, root: str | None) -> bool:
    """Tell whether a file is in the folder asked already.

    Args:
        host: The file's host path.
        folder: The folder below its root, `/`-separated.
        root: The root imposed, host path; None: any root will do.

    Returns:
        True when its folder is that one below the root, or ends with it without a root.
    """
    parent = PureWindowsPath(host).parent.as_posix().casefold()
    asked = folder.strip("/").casefold()
    if root is None:
        return parent.endswith("/" + asked)
    return (
        parent == f"{PureWindowsPath(root).as_posix().casefold().rstrip('/')}/{asked}"
    )
