r"""Where the `mh` script lives, how it is loaded, and the comment lines opening it.

The guides save it in the tool folder of the user's home; `mh folders` and `mh update`
rewrite that very file (0176, 0177), so its header says to use them rather than to
type `launcher` again.
"""

from __future__ import annotations

import os
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import Shell
from media_hygiene.services.next_command import LAUNCHER_VARIABLE

SCRIPT_NAMES: Final = {Shell.POWERSHELL: "mh.ps1", Shell.BASH: "mh.sh"}
_PROFILES: Final = {Shell.POWERSHELL: "$PROFILE", Shell.BASH: "~/.bashrc"}


def script_path(shell: Shell) -> str:
    r"""Where the guides save the script: the tool folder of the user's home.

    Args:
        shell: The shell the script is for.

    Returns:
        `$HOME\media-hygiene\mh.ps1` or `$HOME/media-hygiene/mh.sh`.
    """
    return shell.home_folder(SCRIPT_NAMES[shell])


def load_command(shell: Shell) -> str:
    r"""The command loading the saved script into the current terminal.

    Args:
        shell: The shell the script is for.

    Returns:
        `. "$HOME\media-hygiene\mh.ps1"` or `source "$HOME/media-hygiene/mh.sh"`.
    """
    verb = "." if shell is Shell.POWERSHELL else "source"
    return f'{verb} "{script_path(shell)}"'


def header(shell: Shell) -> tuple[str, ...]:
    """The comment lines opening the script: what it is, how to load it.

    Args:
        shell: The shell the script is for.

    Returns:
        Translated lines, without the comment sign.
    """
    load = load_command(shell)
    profile = _PROFILES[shell]
    return (
        _(
            "media-hygiene launcher: 'mh <command>' runs the tool on your folders, "
            "e.g. mh audit, then mh clean."
        ),
        _("Load it in this terminal with: {load}").format(load=load),
        _("For every terminal, add that line to {profile}.").format(profile=profile),
        _(
            "Another folder? mh folders add <folder>. A new version? mh update. "
            "Both rewrite this file."
        ),
    )


def written(shell: Shell) -> str:
    """The line ending `launcher`: how to load the script just written.

    Args:
        shell: The shell the script is for.

    Returns:
        The line; empty when `mh folders` or `mh update` runs `launcher`: `mh` loads
        the file itself, then shows what it read back.
    """
    if os.environ.get(LAUNCHER_VARIABLE):
        return ""
    return _("Launcher written. Load it with: {load}, then type: mh audit").format(
        load=load_command(shell)
    )
