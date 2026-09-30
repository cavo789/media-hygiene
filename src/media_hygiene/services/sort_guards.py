"""Check, before anything moves, that every destination of a sort is safe.

Each target root must be mounted persistently (not the container's own disk, which
vanishes with it), writable, and outside the protected folders; no file may go into a
protected or excluded folder; a Windows path must stay within its length limit.
Companions whose file edits name different folders are refused too.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError, WorkbookError
from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_writable
from media_hygiene.services.writable import writable_tip

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.sort_plan import SortPlan
    from media_hygiene.services.runtime import Runtime

# Explorer and most Windows programs cannot open a longer path (MAX_PATH, 260 with
# the final NUL).
MAX_WINDOWS_PATH: Final = 259
_WINDOWS: Final = re.compile(r"^[A-Za-z]:\\")
_SHOWN: Final = 5


def check_companions(plan: SortPlan) -> None:
    """Refuse a workbook giving companions (a photo and its video) different folders.

    Args:
        plan: The moves, with the file edits that disagree.

    Raises:
        WorkbookError: Two file edits of one group disagree; nothing was moved.
    """
    if not plan.companions.conflicts:
        return
    raise WorkbookError(
        _(
            "Companions (a photo and its video, a RAW file and its JPEG) travel "
            "together, but their Files cells name different folders; nothing was moved:"
        )
        + "\n"
        + "\n".join(", ".join(cells) for cells in plan.companions.conflicts[:_SHOWN]),
        _(
            "Give them the same folder, or clear all the cells but one, save the "
            "workbook, then run 'sort' again."
        ),
    )


def check_destinations(runtime: Runtime, plan: SortPlan) -> None:
    """Refuse the whole sort when one destination is not safe.

    Args:
        runtime: Settings, mount points and output.
        plan: The moves.

    Raises:
        MountError: A target root is not mounted persistently, or not writable.
        WorkbookError: A destination is protected, excluded, or too long for Windows.
    """
    for root in sorted(plan.roots):
        _check_root(runtime, root)
    mapper = runtime.mapper
    folders = runtime.settings.folders
    kept = [
        mapper.to_container(path) for path in (*folders.protected, *folders.excluded)
    ]
    problems: list[str] = []
    for group in plan.groups:
        host = mapper.to_host(group.folder)
        if any(is_within(group.folder, folder) for folder in kept):
            problems.append(
                _("{folder}: a protected or excluded folder receives no file.").format(
                    folder=host
                )
            )
        for move in group.moves:
            path = mapper.to_host(group.folder / move.source.name)
            if _WINDOWS.match(path) and len(path) > MAX_WINDOWS_PATH:
                problems.append(
                    _("{path}: longer than {count} characters.").format(
                        path=path, count=MAX_WINDOWS_PATH
                    )
                )
    if problems:
        raise WorkbookError(
            _("Some destinations cannot be used; nothing was moved:")
            + "\n"
            + "\n".join(sorted(set(problems))[:_SHOWN]),
            _(
                "Choose other folders (shorter names) in the workbook, save it, and "
                "run 'sort' again."
            ),
        )


def _check_root(runtime: Runtime, root: Path) -> None:
    """Refuse a target root that is lost with the container, protected, or read-only.

    Args:
        runtime: Settings, mount points and output.
        root: A target root (container path).

    Raises:
        MountError: It is not safe to move files into.
    """
    host = runtime.mapper.to_host(root)
    data_dir = runtime.locations.data_dir
    mounted = [r for r in runtime.mounts.data_roots(data_dir) if is_within(root, r)]
    persistent = bool(mounted) and (
        mounted[0] != data_dir or runtime.persistent(MountKind.DATA)
    )
    if not persistent:
        raise MountError(
            _(
                "{path} is not a mounted folder: files moved there would vanish with "
                "the container."
            ).format(path=host),
            _('Mount it, e.g. -v "D:\\Photos sorted:/data/d/Photos sorted".'),
        )
    protected = runtime.settings.folders.protected
    if any(is_within(root, runtime.mapper.to_container(p)) for p in protected):
        raise MountError(
            _(
                "{path} is inside a protected folder: 'sort' never changes those."
            ).format(path=host),
            _(
                "Choose another target with 'classify --target', then edit its new "
                "workbook."
            ),
        )
    existing = next(folder for folder in (root, *root.parents) if folder.exists())
    if not is_writable(existing):
        raise MountError(
            _("The container cannot write to {folders}.").format(folders=host),
            writable_tip((existing,)),
        )
