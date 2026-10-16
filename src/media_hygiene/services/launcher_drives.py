r"""One quarantine per photo drive in `mh` (0183): files set aside stay on their drive.

With the default quarantine (`$HOME\media-hygiene\quarantine`, on `C:`), each other
drive of the photo folders gets `E:\media-hygiene\quarantine` (from
WSL `/mnt/e/media-hygiene/quarantine`) mounted on `/quarantine/e`; `mh` creates the
folder before each run like those of the home. A whole drive given as photos (`E:\`)
gets one too: the audit never reads a `media-hygiene` folder (`scan/skipped_dirs.py`).
`mh folders add` writes `mh` again, so a new drive gets its own. A quarantine the user
named (`--quarantine`, a `-v` of their own) receives every drive's files: none is added
(0193); `clean` then says the copy crosses drives (0182).
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
    """Add a quarantine for each photo drive but C:, unless the user named theirs.

    Args:
        script: The script, its photo folders final.

    Returns:
        The script, with these mounts and the folders `mh` creates for them (the
        same script again when it had them already).
    """
    quarantine = script.tools[TOOL_KINDS.index(MountKind.QUARANTINE)]
    named = quarantine.host != script.shell.home_folder(MountKind.QUARANTINE.value)
    volumes: dict[str, Volume] = {}
    for volume in () if named else script.data:
        letter = _letter(volume.host)
        if letter is None or letter == _HOME_DRIVE or letter in volumes:
            continue
        volumes[letter] = Volume(
            _quarantine_of(volume.host, letter), quarantine.point / letter
        )
    drives = tuple(volumes[letter] for letter in sorted(volumes))
    hosts = tuple(volume.host for volume in drives)
    before = {volume.host for volume in script.drives}
    created = (
        *(folder for folder in script.created if folder not in {*hosts, *before}),
        *hosts,
    )
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
