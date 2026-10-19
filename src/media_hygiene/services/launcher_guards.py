"""What `mh` checks before a `docker run`: the page port, a removable drive.

A page left by a closed window (0250): closing a console with its X kills the
`docker` client, not the container, which keeps the port of the pages and its mounts
(measured on Windows, 2026-10-19). Each page container carries the shell and the PID
of its console in a label, with the console's start time: Windows gives the PID of a
closed console to another process, so a PID alone could make a dead page look live.
Before a page, `mh` stops one whose console is gone, says it in one line, and
leaves a page whose console still runs, telling the user to close it there.
Never Docker's raw "port is already allocated".

A removable drive (0252): WSL mounts fixed drives only, so Docker Desktop shows an
empty folder for a USB stick. `mh.ps1` mounts it in Docker Desktop's VM first
(`wsl.exe`, measured to work on FAT32), one line said; a failure stops the command
with the advice. After the run, a drive `mh` mounted itself is unmounted, so that
Windows can eject the stick; left mounted while another `mh` container uses it (each
container carries a label per removable drive it mounts).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.services.launcher_menu import shell_safe, with_variable

# The label of a page container: `<shell>-<PID>-<start time of its console>`,
# e.g. `powershell-4242-20261019175220` (an older `mh` wrote `powershell-4242`).
PAGE_LABEL: Final = "media-hygiene.page"
# The label of a container using a removable drive: `media-hygiene.drive.<letter>=1`.
DRIVE_LABEL: Final = "media-hygiene.drive"
# The WSL distribution of Docker Desktop's VM, where a removable drive is mounted.
DESKTOP_DISTRO: Final = "docker-desktop"


@dataclass(frozen=True, slots=True)
class GuardTexts:
    """The lines of the checks, ready to sit inside double quotes."""

    stopped: str  # a page whose console is gone: stopped
    open: str  # a page whose console still runs: left alone
    held: str  # the port held by another container; holds `${id}`
    shared: str  # mh.ps1: a removable drive mounted in the VM; holds `${drive}`
    unshared: str  # mh.ps1: mounting it failed; holds `${drive}`
    kept: str  # mh.ps1: left mounted, another mh container uses it; holds `${drive}`
    stuck: str  # mh.ps1: unmounting it failed; holds `${drive}`


@dataclass(frozen=True, slots=True)
class LauncherGuards:
    """The labels of the containers, the VM's distribution and the lines said."""

    label: str
    drive: str
    distro: str
    texts: GuardTexts


def launcher_guards() -> LauncherGuards:
    """Translate the lines of the checks, the shell variables in place.

    Returns:
        The label, the distribution and the lines.
    """
    return LauncherGuards(
        label=PAGE_LABEL,
        drive=DRIVE_LABEL,
        distro=DESKTOP_DISTRO,
        texts=GuardTexts(
            stopped=shell_safe(
                _("An mh page left open by a closed window was stopped.")
            ),
            open=shell_safe(
                _(
                    "An mh page is open in another window: close it there (Ctrl+C), "
                    "then type the command again."
                )
            ),
            held=with_variable(
                _(
                    "The port of the mh pages is held by the container {id}: close "
                    "the window where it runs, or type docker stop {id}, then type "
                    "the command again."
                ),
                "{id}",
                "${id}",
            ),
            shared=with_variable(
                _("{drive}: is a removable drive: shared with Docker Desktop."),
                "{drive}",
                "${drive}",
            ),
            unshared=with_variable(
                _(
                    "Docker Desktop cannot see {drive}: (a removable drive, such as a "
                    "USB stick), and sharing it failed: copy the folder to a fixed "
                    "disk, or use an external hard disk."
                ),
                "{drive}",
                "${drive}",
            ),
            kept=with_variable(
                _(
                    "{drive}: stays shared with Docker Desktop: another mh window "
                    "uses it."
                ),
                "{drive}",
                "${drive}",
            ),
            stuck=with_variable(
                _(
                    "{drive}: could not be unshared from Docker Desktop: if Windows "
                    "refuses to eject it, quit Docker Desktop first."
                ),
                "{drive}",
                "${drive}",
            ),
        ),
    )
