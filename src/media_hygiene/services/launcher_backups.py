r"""The backups of `launcher --backup "E:\Backup"`: mounted read-only, always (0205).

A backup (0204) is compared, never changed. `mh` mounts the photo folders read-write
for the commands that change them (`clean`, `sort`…); a backup gets its own mounts,
`:ro` for every command, `clean` included, so the operating system itself refuses
any change. The commands that take `--backup` get it, one per folder: the Windows
path in `mh.ps1` (the mount table maps it), the mount point in `mh.sh` (a WSL
`/mnt/e/…` is no path of the container).
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import Volume
from media_hygiene.services.launcher_folders import container_point

if TYPE_CHECKING:
    from media_hygiene.services.launcher import LauncherScript
    from media_hygiene.services.runtime import Runtime

_WINDOWS: Final = re.compile(r"^[A-Za-z]:")


def with_backups(
    runtime: Runtime, script: LauncherScript, hosts: tuple[str, ...]
) -> LauncherScript:
    """Add the backup folders typed to the script, apart from the photo folders.

    Args:
        runtime: Settings and mount points.
        script: The script, its photo folders already in.
        hosts: The folders of `--backup`, as typed.

    Returns:
        The script with these backups; unchanged without any.

    Raises:
        MountError: A backup that is, holds or lies in a photo folder or another
            backup: its files would be both compared and cleaned.
    """
    if not hosts:
        return script
    data_dir = runtime.locations.data_dir
    backups = tuple(
        Volume(host.rstrip("\\/") or host, container_point(data_dir, host))
        for host in dict.fromkeys(hosts)
    )
    for backup in backups:
        for other in (*script.data, *backups):
            if other is not backup and _overlap(backup.host, other.host):
                raise MountError(
                    _("{backup} overlaps {folder}: give them apart.").format(
                        backup=backup.host, folder=other.host
                    ),
                    _(
                        "A backup is compared, never changed: it cannot be, hold or "
                        "lie in a photo folder or another backup."
                    ),
                )
    return replace(script, backups=backups)


def _overlap(first: str, second: str) -> bool:
    """Tell whether two host folders are the same, or one holds the other.

    Windows ignores case, so Windows folders are compared without it.

    Args:
        first: A host folder.
        second: Another one.

    Returns:
        True when they share files.
    """
    one: PurePath
    two: PurePath
    if _WINDOWS.match(first) and _WINDOWS.match(second):
        # `E:` alone is relative to E:'s current folder: `E:/` is the drive.
        one, two = PureWindowsPath(f"{first}/"), PureWindowsPath(f"{second}/")
    else:
        one, two = PurePosixPath(first), PurePosixPath(second)
    return one == two or one.is_relative_to(two) or two.is_relative_to(one)
