"""Which folders `sort` and `clean` may remove once they left them empty (0202)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.clean_folders import EmptiedFolders
from media_hygiene.actions.sort_folders import FolderRules
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.services.runtime import Runtime


def base_rules(runtime: Runtime) -> FolderRules:
    r"""The folders never removed, and the junk that does not keep one alive.

    Stops: the data dir, its folders (`/data/c` stands for a drive: `C:\`), the
    mounted folders and every mount point. Kept, with all below them: the
    protected, backup and excluded folders.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The rules both commands share.
    """
    data_dir, settings = runtime.locations.data_dir, runtime.settings
    roots = {*runtime.mounts.data_roots(data_dir), *_drives(data_dir)}
    kept = (*settings.folders.untouched, *settings.folders.excluded)
    return FolderRules(
        junk=settings.sort.junk_names,
        stops=frozenset({data_dir, *roots, *runtime.mounts.mount_points}),
        kept=tuple(runtime.mapper.to_container(path) for path in kept),
        quarantine=runtime.persistent(MountKind.QUARANTINE),
    )


def emptied_by(runtime: Runtime, plan: CleanPlan) -> EmptiedFolders:
    """The folders a clean may leave empty.

    Args:
        runtime: Settings, mount points and output.
        plan: What the clean does.

    Returns:
        The candidates and their rules.
    """
    return EmptiedFolders.of(plan, base_rules(runtime))


def _drives(data_dir: Path) -> set[Path]:
    """The folders right below the data dir: one per drive letter.

    Args:
        data_dir: The directory holding the folders to analyse.

    Returns:
        Them; none when it cannot be read.
    """
    try:
        with os.scandir(data_dir) as entries:
            return {Path(entry.path) for entry in entries if entry.is_dir()}
    except OSError:
        return set()
