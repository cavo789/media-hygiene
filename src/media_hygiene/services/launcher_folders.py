r"""The folders of `launcher --photos "C:\Photos" --quarantine "D:\q"`: no `-v`.

`launcher` does not need to see the photos: it only writes the script. A folder given
as Explorer shows it gets its mount point by the convention of `paths/host_paths.py`
(`C:\Photos` → `/data/c/Photos`; from WSL `/mnt/c/Photos` → `/data/c/Photos`), so both
sides of a `-v` can no longer disagree. The folders mounted with `-v` stay, merged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import Shell, Volume, guess_shell
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.launcher import LauncherScript
    from media_hygiene.services.runtime import Runtime

_DRIVE: Final = re.compile(r"^(?P<drive>[A-Za-z]):[\\/]*(?P<rest>.*)$")
_WSL_DRIVE: Final = re.compile(r"^/mnt/(?P<drive>[a-z])(?:/(?P<rest>.*))?$")
_SEPARATORS: Final = re.compile(r"[\\/]+")


@dataclass(frozen=True, slots=True)
class FolderChoice:
    """The folders typed on the command line of `launcher`."""

    photos: tuple[str, ...] = ()
    quarantine: str | None = None

    def shell(self) -> Shell | None:
        """The shell these folders are written for.

        Returns:
            PowerShell for a Windows path, bash for another, None without folders.
        """
        hosts = (*self.photos, *((self.quarantine,) if self.quarantine else ()))
        return guess_shell(hosts) if hosts else None


def container_point(data_dir: Path, host: str) -> Path:
    r"""Where a host folder is mounted, by the convention of the whole tool.

    Args:
        data_dir: The data mount point (`/data`).
        host: `C:\Photos`, `/mnt/c/Photos` or `/home/me/Pictures`, absolute.

    Returns:
        `/data/c/Photos`, `/data/c/Photos` or `/data/home/me/Pictures`.

    Raises:
        MountError: A network or relative path: no mount point to give it.
    """
    windows = _DRIVE.match(host)
    wsl = _WSL_DRIVE.match(host)
    match = windows or wsl
    if match is not None:
        rest = [part for part in _SEPARATORS.split(match["rest"] or "") if part]
        return data_dir.joinpath(match["drive"].lower(), *rest)
    if host.startswith(("\\\\", "//")):
        raise MountError(
            _("{folder}: a network folder, which --photos does not take.").format(
                folder=host
            ),
            _("Copy the photos to a local disk, or mount it yourself with -v."),
        )
    if not host.startswith("/"):
        raise MountError(
            _("{folder}: give the full path, from the drive letter.").format(
                folder=host
            )
        )
    return data_dir.joinpath(*PurePosixPath(host).parts[1:])


def with_folders(
    runtime: Runtime, script: LauncherScript, choice: FolderChoice
) -> LauncherScript:
    """Add the photo folders typed, and the quarantine typed, to the script.

    Args:
        runtime: Settings and mount points.
        script: The script built from the mounts of this run.
        choice: The folders of `--photos` and `--quarantine`.

    Returns:
        The script, with these folders; unchanged without any.
    """
    data_dir = runtime.locations.data_dir
    given = tuple(
        Volume(host.rstrip("\\/") or host, container_point(data_dir, host))
        for host in dict.fromkeys(choice.photos)
    )
    data = (*script.data, *(volume for volume in given if volume not in script.data))
    _refuse_nested(data)
    if choice.quarantine is None:
        return replace(script, data=data)
    point = runtime.locations.path_of(MountKind.QUARANTINE)
    container_point(data_dir, choice.quarantine)  # the same refusals
    tools = tuple(
        Volume(choice.quarantine, point) if volume.point == point else volume
        for volume in script.tools
    )
    default = script.shell.home_folder(MountKind.QUARANTINE.value)
    created = tuple(folder for folder in script.created if folder != default)
    return replace(script, data=data, tools=tools, created=created)


def checked_folders(script: LauncherScript) -> tuple[str, ...]:
    """The photo folders `mh` checks before each run: host paths, not volumes.

    Args:
        script: The script.

    Returns:
        The host folders that are paths (a named volume is not).
    """
    return tuple(
        volume.host
        for volume in script.data
        if _DRIVE.match(volume.host) or volume.host.startswith("/")
    )


def _refuse_nested(data: tuple[Volume, ...]) -> None:
    """Refuse a folder given inside another one: each file would be seen twice.

    Windows ignores case, so Windows folders are compared without it.

    Args:
        data: Every photo folder of the script.

    Raises:
        MountError: One folder holds another.
    """
    for inner in data:
        for outer in data:
            if inner is not outer and _inside(inner.host, outer.host):
                raise MountError(
                    _("{inner} is inside {outer}: give only {outer}.").format(
                        inner=inner.host, outer=outer.host
                    ),
                    _("Each of its files would be seen twice, as its own duplicate."),
                )


def _inside(inner: str, outer: str) -> bool:
    """Tell whether a host folder lies inside another one.

    Args:
        inner: A host folder.
        outer: Another one.

    Returns:
        True when `inner` is below `outer` (not the same folder).
    """
    flavour = (
        PureWindowsPath
        if _DRIVE.match(inner) and _DRIVE.match(outer)
        else PurePosixPath
    )
    inside, around = flavour(inner), flavour(outer)
    return inside != around and inside.is_relative_to(around)
