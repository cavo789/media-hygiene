r"""One quarantine per photo drive in `mh` (0183): files set aside stay on their drive.

Each drive of the photo folders other than the quarantine's own (`C:`, the user's
home, unless `--quarantine` names another) gets `E:\media-hygiene\quarantine` (from
WSL `/mnt/e/media-hygiene/quarantine`) mounted on `/quarantine/e`; `mh` creates the
folder before each run like those of the home. A drive whose photo folder holds that
folder (`E:\` itself) gets none: the quarantine would be read as photos; its files go
to `/quarantine`. `mh folders add` writes `mh` again, so a new drive gets its own.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.docker_run import TOOL_HOME, Volume
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.next_command import TOOL_KINDS

if TYPE_CHECKING:
    from media_hygiene.services.launcher import LauncherScript

_WINDOWS: Final = re.compile(r"^(?P<letter>[A-Za-z]):(?:[\\/]|$)")
_WSL: Final = re.compile(r"^/mnt/(?P<letter>[a-z])(?:/|$)")
_HOME_DRIVE: Final = "c"  # `$HOME`: on Windows and under WSL, the system drive


def with_drive_quarantines(script: LauncherScript) -> LauncherScript:
    """Add a quarantine for each photo drive that is not the quarantine's own.

    Args:
        script: The script, its photo folders final.

    Returns:
        The script, with these mounts and the folders `mh` creates for them (the
        same script again when it had them already).
    """
    quarantine = script.tools[TOOL_KINDS.index(MountKind.QUARANTINE)]
    own = _letter(quarantine.host) or _HOME_DRIVE
    volumes: dict[str, Volume] = {}
    for volume in script.data:
        letter = _letter(volume.host)
        if letter is None or letter == own or letter in volumes:
            continue
        host = _quarantine_of(volume.host, letter)
        if not any(_holds(data.host, host) for data in script.data):
            volumes[letter] = Volume(host, quarantine.point / letter)
    drives = tuple(volumes[letter] for letter in sorted(volumes))
    hosts = tuple(volume.host for volume in drives)
    created = (*(folder for folder in script.created if folder not in hosts), *hosts)
    return replace(script, drives=drives, created=created)


def _letter(host: str) -> str | None:
    r"""The drive letter of a host folder.

    Args:
        host: `E:\Photos`, `/mnt/e/Photos`, `$HOME\…`, a named volume.

    Returns:
        `e`; None for a folder without a drive letter.
    """
    match = _WINDOWS.match(host) or _WSL.match(host)
    return match["letter"].lower() if match else None


def _quarantine_of(host: str, letter: str) -> str:
    r"""The quarantine folder of a drive, written like the photo folder that names it.

    Args:
        host: A photo folder of that drive.
        letter: Its drive letter.

    Returns:
        `E:\media-hygiene\quarantine` or `/mnt/e/media-hygiene/quarantine`.
    """
    name = MountKind.QUARANTINE.value
    if _WINDOWS.match(host):
        return str(PureWindowsPath(f"{letter.upper()}:\\", TOOL_HOME, name))
    return str(PurePosixPath("/mnt", letter, TOOL_HOME, name))


def _holds(photos: str, folder: str) -> bool:
    """Tell whether a photo folder holds a folder (Windows ignores case).

    Args:
        photos: A photo folder.
        folder: The quarantine of a drive.

    Returns:
        True when the folder is inside the photo folder, or is it.
    """
    if _WINDOWS.match(photos) and _WINDOWS.match(folder):
        around = PureWindowsPath(photos.rstrip("\\/") + "\\")  # `E:` is `E:\`
        return PureWindowsPath(folder).is_relative_to(around)
    return PurePosixPath(folder).is_relative_to(PurePosixPath(photos))
