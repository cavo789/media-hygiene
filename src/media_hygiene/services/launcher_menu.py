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

from media_hygiene.constants import ExitCode
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

# Inside the double-quoted strings of both shells, these would be code, not text.
UNSAFE_CHARACTERS = frozenset('"$`\\')
# How long `mh` waits for a page to answer before opening the browser on it (0178): a
# review audits first, minutes without a cache. The wait also ends with the command.
BROWSE_WAIT: Final = 300
# How long `docker desktop start` may take before `mh` gives up (0200): a cold start
# after a reboot, not a setting (step 16 of `mh-measure.ps1` times it).
DESKTOP_WAIT: Final = 180
_COMMAND: Final = f"{LAUNCHER_FUNCTION} ${{command}}"


@dataclass(frozen=True, slots=True)
class Crash:
    """How `mh` tells a crash of the home server, and how often it starts it again."""

    codes: tuple[int, ...]  # its own code, and Docker's kill (out of memory)
    window: int  # two crashes within these seconds end `mh`'s loop (0365)


CRASH: Final = Crash((int(ExitCode.CRASHED), int(ExitCode.KILLED)), 60)


@dataclass(frozen=True, slots=True)
class Remount:
    """How `mh` follows a photo folder plugged in or removed during a session (0359)."""

    code: int  # what its watch returns once it stopped the server to mount again
    ticks: int  # the folders checked every `ticks` polls of 250 ms (Test-Path: ms)


REMOUNT: Final = Remount(int(ExitCode.REMOUNT), 12)


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
    starting: str  # mh.ps1: Docker Desktop does not answer, `mh` starts it (0200)
    ready: str  # mh.ps1: started after a failed run: the command is typed again
    running: str  # `mh` alone: the page runs in the background, its window kept open
    crashed: str  # the home server stopped unexpectedly: started again (0365)
    crashed_again: str  # the same within a minute: the loop ends
    unplugged: str  # the home server starts without a missing folder; holds `${folder}`
    remounted: str  # a photo folder came or left: the server started again with it
    crash: Crash = CRASH  # the codes of a crash, and its window
    remount: Remount = REMOUNT  # 0359


def menu_texts() -> MenuTexts:
    """Translate the messages of `mh` itself, the shell variables in place.

    Returns:
        The messages; a translation's quote or dollar sign is dropped, so that it
        cannot break the script.
    """
    return MenuTexts(
        prompt=shell_safe(_("Step number (Enter: the proposed one)")),
        unknown=shell_safe(
            _("No step {choice}: type mh menu to see the menu again.")
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
        starting=shell_safe(
            ngettext(
                "Docker Desktop is not started: starting it (up to {minutes} minute)…",
                "Docker Desktop is not started: starting it (up to {minutes} minutes)…",
                DESKTOP_WAIT // 60,
            ).format(minutes=DESKTOP_WAIT // 60)
        ),
        ready=shell_safe(
            _("Docker Desktop is ready: type the command again (↑ then Enter).")
        ),
        running=shell_safe(
            _(
                "Media Hygiene is running: its page opens in your browser. Keep this "
                "window open (minimised is fine): closing it stops Media Hygiene."
            )
        ),
        crashed=shell_safe(_("The home page stopped unexpectedly: started again.")),
        unplugged=shell_safe(_("{folder}: not plugged in, shown once it is.")).replace(
            "{folder}", "${folder}"
        ),
        remounted=shell_safe(
            _("A photo folder was plugged in or removed: the home page follows it.")
        ),
        crashed_again=shell_safe(
            _(
                "The home page stopped unexpectedly twice in a row: type mh to start "
                "it again."
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
