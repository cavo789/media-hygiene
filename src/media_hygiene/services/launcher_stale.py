"""`mh` noticing that its own file changed since the window loaded it (0276).

A terminal keeps the function it loaded: a script written again by `launcher` (or by
`mh update`, from another window) is not read until it is loaded again, so an old `mh`
kept running with the old behaviour and nothing said so. Before each command, one stat
of the file: if it differs from the one recorded at load time, one line says how to load
it again. The file removed or moved: nothing is said (the call still works from memory).
"""

from __future__ import annotations

from dataclasses import dataclass

from media_hygiene.i18n import _
from media_hygiene.services.launcher_menu import shell_safe
from media_hygiene.services.next_command import LAUNCHER_FUNCTION


@dataclass(frozen=True, slots=True)
class StaleTexts:
    """The line said when the loaded script is out of date."""

    changed: str  # holds `${reload}`: the command loading the file again


def stale_texts() -> StaleTexts:
    """Translate the line said when the script changed since it was loaded.

    Returns:
        The line, `${reload}` in place of the command to type.
    """
    text = shell_safe(
        _(
            "{command} changed on disk since this window loaded it: type {reload} "
            "(or open a new window)."
        )
    )
    return StaleTexts(
        changed=text.replace("{command}", LAUNCHER_FUNCTION).replace(
            "{reload}", "${reload}"
        )
    )
