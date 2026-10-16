r"""The commands `mh` runs on the host itself, without `docker run` (0175-0181).

The container can neither open a browser nor write a Windows shortcut or registry key:
`mh open` (the reports in the browser), `mh shortcut` (an icon opening the menu) and
`mh explorer` (the right-click entry of a folder) are functions of the script, and so
are `mh folders` and `mh update`, which write the script itself again. `mh`
dispatches them before anything else, by their first word; the bash script says that
`shortcut` and `explorer` are for Windows. Their messages are written into the
script, translated, with the shell variables they show (`${index}`, `${path}`,
`${key}`, `$1`).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.launcher_menu import shell_safe, with_variable
from media_hygiene.services.next_command import (
    LAUNCHER_FUNCTION,
    LAUNCHER_VARIABLE,
    TOOL_KINDS,
)

if TYPE_CHECKING:
    from media_hygiene.services.launcher import LauncherScript

OPEN: Final = "open"
SHORTCUT: Final = "shortcut"
EXPLORER: Final = "explorer"
# Both write `mh` again by running `launcher` (0176, 0177: `launcher_kept.py`).
FOLDERS: Final = "folders"
UPDATE: Final = "update"
HOST_COMMANDS: Final = (OPEN, SHORTCUT, EXPLORER, FOLDERS, UPDATE)
WINDOWS_ONLY: Final = (SHORTCUT, EXPLORER)
# The name of the shortcut and of the right-click entry.
LABEL: Final = "Media Hygiene"
# HKCU: the user's own key, no administrator needed.
EXPLORER_KEY: Final = r"HKCU:\Software\Classes\Directory\shell\MediaHygiene"
# Explorer puts the folder after a `#`: a comment for PowerShell, so that no character
# of its name (an apostrophe) breaks the command; `mh` reads it from the command line.
FROM_EXPLORER: Final = "--from-explorer"
_INDEX_PAGE: Final = "index.html"
_VOLUME: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


@dataclass(frozen=True, slots=True)
class HostTexts:  # pylint: disable=too-many-instance-attributes  # one per message
    """The messages of the host commands, ready to sit inside double quotes."""

    no_report: str
    volume: str  # the reports are in a named volume
    no_opener: str  # holds `$index`
    windows: str  # holds `mh $1`
    no_file: str
    saved: str  # holds `$path`
    not_saved: str  # holds `$path`
    shortcut: str
    explorer: str  # holds `$key`
    removed: str  # holds `$key`
    not_removed: str  # holds `$key`


@dataclass(frozen=True, slots=True)
class HostCommands:
    """What the script needs to run its host commands."""

    names: tuple[str, ...]
    windows: tuple[str, ...]
    index: str  # the host path of the reports' `index.html`; empty for a volume
    texts: HostTexts
    label: str = LABEL
    key: str = EXPLORER_KEY
    flag: str = FROM_EXPLORER


def host_commands(script: LauncherScript) -> HostCommands:
    """Gather the host commands of a script, with the host folder of its reports.

    Args:
        script: The script.

    Returns:
        The commands, their messages translated.
    """
    reports = script.tools[TOOL_KINDS.index(MountKind.REPORTS)].host
    separator = "\\" if script.shell is Shell.POWERSHELL else "/"
    folder = reports.rstrip("/\\")
    return HostCommands(
        names=HOST_COMMANDS,
        windows=WINDOWS_ONLY,
        index="" if _VOLUME.fullmatch(reports) else f"{folder}{separator}{_INDEX_PAGE}",
        texts=_texts(reports),
    )


def windows_menu() -> bool:
    """Tell whether the menu offers the Windows steps: not to the bash `mh`.

    Returns:
        False when `mh.sh` runs the image (it says its shell), True otherwise.
    """
    return os.environ.get(LAUNCHER_VARIABLE) != Shell.BASH.value


def _texts(reports: str) -> HostTexts:
    """Translate the messages of the host commands, the shell variables in place.

    Args:
        reports: The host folder (or volume) of the reports.

    Returns:
        The messages, without what a double-quoted string would read as code.
    """
    audit = f"{LAUNCHER_FUNCTION} audit"
    return HostTexts(
        no_report=shell_safe(_("No report yet: type {command} first.")).replace(
            "{command}", audit
        ),
        volume=shell_safe(
            _(
                "The reports are in the Docker volume {volume}, which no browser "
                "opens: write mh again with launcher and "
                "-v <a folder of yours>:/reports."
            )
        ).replace("{volume}", shell_safe(reports)),
        no_opener=shell_safe(
            _("No program here opens a page: open {index} yourself.")
        ).replace("{index}", "${index}"),
        windows=shell_safe(_("{command} is for Windows only.")).replace(
            "{command}", f"{LAUNCHER_FUNCTION} $1"
        ),
        no_file=shell_safe(
            _(
                "mh was not loaded from its file mh.ps1: load it as step 0 of the "
                "guides says, then try again."
            )
        ),
        saved=with_variable(_("Saved, read back from {path}:"), "{path}", "${path}"),
        not_saved=with_variable(_("Could not write {path}."), "{path}", "${path}"),
        shortcut=shell_safe(
            _(
                "Double-click Media Hygiene on the Desktop or in the Start menu: "
                "the mh menu opens."
            )
        ),
        explorer=with_variable(
            _(
                "Right-click a folder, then Media Hygiene: the mh menu opens on it. "
                "Read back from {key}:"
            ),
            "{key}",
            "${key}",
        ),
        removed=with_variable(
            _("Right-click entry removed: {key} is gone."), "{key}", "${key}"
        ),
        not_removed=with_variable(_("Could not remove {key}."), "{key}", "${key}"),
    )
