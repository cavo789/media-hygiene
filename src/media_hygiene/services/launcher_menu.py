"""What `mh` says by itself: the menu's prompt, a folder not found, a long run's end.

The `menu` command prints the steps; the `mh` function asks for the number and runs
the step itself (`services/launcher.py`), after checking the photo folders. Its
messages are written into the script, translated, with the shell variables they show
(`${choice}`, `${chosen}`, `${folder}`, `${command}`, `${shown}`): braced,
so that a colon after them (`mh ${command}: done`) is text, not a drive or scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

# Inside the double-quoted strings of both shells, these would be code, not text.
UNSAFE_CHARACTERS = frozenset('"$`\\')
# How long `mh` waits for a page to answer before opening the browser on it (0178): a
# review audits first, minutes without a cache. The wait also ends with the command.
BROWSE_WAIT: Final = 300
_COMMAND: Final = f"{LAUNCHER_FUNCTION} ${{command}}"


@dataclass(frozen=True, slots=True)
class MenuTexts:  # pylint: disable=too-many-instance-attributes  # one per message
    """The messages of `mh` itself, ready to sit inside double quotes."""

    prompt: str
    unknown: str  # holds `${choice}`
    direct: str  # holds `mh ${chosen}`
    missing: str  # holds `${folder}`
    done: str  # the window title after a long run; holds `mh ${command}`
    failed: str  # the same, when it failed
    folder: str  # `mh --photos X` alone: the menu's folder; holds `${shown}` (0181)
    reading: str  # shown while the menu reads the tool folders (a large quarantine: s)
    desktop: str  # mh.ps1: a failed run, and Docker Desktop does not answer (0174)
    daemon: str  # mh.sh: the same, Docker on Linux, macOS or WSL


def menu_texts() -> MenuTexts:
    """Translate the messages of `mh` itself, the shell variables in place.

    Returns:
        The messages; a translation's quote or dollar sign is dropped, so that it
        cannot break the script.
    """
    return MenuTexts(
        prompt=shell_safe(_("Step number (Enter: the proposed one)")),
        unknown=shell_safe(
            _("No step {choice}: type mh alone to see the menu again.")
        ).replace("{choice}", "${choice}"),
        direct=shell_safe(_("Next time, type it directly: {command}")).replace(
            "{command}", f"{LAUNCHER_FUNCTION} ${{chosen}}"
        ),
        missing=shell_safe(
            _(
                "{folder} cannot be found: plug its disk in, or write mh again with "
                "launcher."
            )
        ).replace("{folder}", "${folder}"),
        done=shell_safe(_("{command}: done")).replace("{command}", _COMMAND),
        failed=shell_safe(_("{command}: failed")).replace("{command}", _COMMAND),
        folder=shell_safe(_("The step you choose also analyses: {folder}")).replace(
            "{folder}", "${shown}"
        ),
        reading=shell_safe(_("Reading where you are…")),
        desktop=shell_safe(
            _(
                "Docker Desktop is not started: start it from the Start menu, wait "
                "until it says it is running, then type the command again."
            )
        ),
        daemon=shell_safe(
            _(
                "Docker is not started: start it (Docker Desktop, or the docker "
                "service), then type the command again."
            )
        ),
    )


def shell_safe(text: str) -> str:
    """Drop what a double-quoted string would read as code.

    Args:
        text: A translated message.

    Returns:
        The message without quotes, dollars, backticks nor backslashes.
    """
    return "".join(
        character for character in text if character not in UNSAFE_CHARACTERS
    )


def with_variable(text: str, field: str, variable: str) -> str:
    """Make a message safe, then put a shell variable in its field.

    Args:
        text: The translated message.
        field: Its field, e.g. `{path}`.
        variable: The shell variable shown there, e.g. `${path}`.

    Returns:
        The message for the script.
    """
    return shell_safe(text).replace(field, variable)
