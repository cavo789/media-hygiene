"""How the shortcut and the right-click entry start `mh`: no execution policy bypassed.

`mh shortcut` and `mh explorer` (0180, 0181) wrote `powershell.exe -ExecutionPolicy
Bypass`: Avast's Behavior Shield stopped such a start (IDP.HELU.PSD11, measured twice on
2026-10-19), and an antivirus exception is no answer. Every user already set
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (step 1 of the guides), which lets
PowerShell load an `mh.ps1` written on the PC: the start loads it as it is (0257). When
the policy still refuses it, the window says that line instead of PowerShell's error.

A shortcut or an entry written before keeps its old command: loading `mh.ps1` (at
`mh update`, `mh folders`, or after `launcher`) writes again those that start this very
file with another command, reads them back and says so in one line each.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.services.launcher_menu import shell_safe, with_variable

# The line that lets PowerShell load a script written on the PC (step 1 of the guides).
POLICY_LINE: Final = "Set-ExecutionPolicy -Scope CurrentUser RemoteSigned"
# What no command line `mh` writes may hold: each one is what antivirus heuristics flag.
FLAGGED: Final = (
    "Bypass",
    "-EncodedCommand",
    "Invoke-Expression",
    "WindowStyle Hidden",
    "conhost",
)
_SINGLE_QUOTE: Final = "'"


@dataclass(frozen=True, slots=True)
class LaunchTexts:
    """The lines of the start and of its refresh, ready for double quotes."""

    policy: str  # sits inside single quotes, in the command line of the start
    refreshed: str  # holds `${path}`


def launch_texts() -> LaunchTexts:
    """Translate the lines of the start and of the refresh of an older start.

    Returns:
        The lines, without what a double-quoted string would read as code; the policy
        line with its single quotes doubled, as a single-quoted string needs.
    """
    policy = _(
        "PowerShell refused to load mh.ps1. Type this line once, then start "
        "Media Hygiene again: {line}"
    ).replace("{line}", POLICY_LINE)
    return LaunchTexts(
        policy=shell_safe(policy).replace(_SINGLE_QUOTE, _SINGLE_QUOTE * 2),
        refreshed=with_variable(
            _("Brought up to date, read back from {path}: it starts this mh."),
            "{path}",
            "${path}",
        ),
    )
