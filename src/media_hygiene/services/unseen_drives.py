"""Refuse a folder Docker Desktop shows empty: never compare with nothing (0252).

WSL mounts fixed drives only: a removable one (a USB stick) plugged into Windows is not
shared, and Docker Desktop mounts an empty folder of its own disk in its place. An
audit then says the photos are missing from a backup that holds them all.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def refuse_unseen_drives(runtime: Runtime) -> None:
    r"""Stop when a mounted folder lies on a drive Docker Desktop cannot see.

    Args:
        runtime: Mount points.

    Raises:
        MountError: Naming the folders (`D:\Photos`) and how to share their drive.
    """
    unseen = [folder for _point, folder in runtime.mounts.unseen_drives]
    if not unseen:
        return
    drive = unseen[0][0]
    raise MountError(
        ngettext(
            "Docker Desktop cannot see {folders} (a removable drive, such as a USB "
            "stick): it shows an empty folder instead, so nothing is compared.",
            "Docker Desktop cannot see {folders} (a removable drive, such as a USB "
            "stick): it shows empty folders instead, so nothing is compared.",
            len(unseen),
        ).format(folders=", ".join(unseen)),
        _(
            "Start the command with mh, which shares such a drive with Docker "
            "Desktop; or share it yourself in PowerShell, then start the command "
            "again: {command} (or copy the folder to a fixed disk)."
        ).format(command=share_command(drive)),
    )


def share_command(drive: str) -> str:
    """The PowerShell line mounting a drive in Docker Desktop's VM, as `mh` does.

    Args:
        drive: The drive letter, any case.

    Returns:
        The `wsl -d docker-desktop` command line.
    """
    letter = drive.lower()
    return (
        f'wsl -d docker-desktop sh -c "mkdir -p /mnt/host/{letter} && '
        f'mount -t drvfs {letter.upper()}: /mnt/host/{letter}"'
    )
