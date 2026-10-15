r"""What `launcher` prints instead of the launcher: run with `-it`, or a folder refused.

The output goes into `> mh.ps1` whatever happens, so a refusal is itself a script:
comment lines to read, then one line stopping the load with the same advice. With
`-t`, Docker even joins stderr to stdout in one pseudo-terminal: whatever the command
says lands in the file, not on the screen.
PowerShell 5.1 decodes the output of `docker` with the console code page before
writing the file, so that line spells every non-ASCII character as `[char]` codes.
"""

from __future__ import annotations

from typing import Final

from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import Shell
from media_hygiene.services.launcher import script_path

_LAST_ASCII: Final = 0x7F
# The pseudo-terminal ends lines with \r\n: the final comment sign swallows the \r.
_BASH_STOP: Final = "printf '%s\\n' {text} >&2; return 2 2>/dev/null || exit 2 #"


def refusal_script(shell: Shell) -> str:
    """The script saying to run the launcher again, without `-it`.

    Args:
        shell: The shell the launcher is for.

    Returns:
        Readable comment lines, then the line that stops loading the script.
    """
    lines = (
        _("Nothing written: the launcher goes into a file, not on the screen."),
        _("Run the same command without -it, ending with: > {path}").format(
            path=f'"{script_path(shell)}"'
        ),
    )
    return stopping_script(shell, lines)


def stopping_script(shell: Shell, lines: tuple[str, ...]) -> str:
    """A script that says why nothing was written, then stops its own loading.

    Args:
        shell: The shell the launcher is for.
        lines: The translated advice, one sentence per line.

    Returns:
        Readable comment lines, then the line that stops loading the script.
    """
    message = " ".join(lines)
    stop = (
        f"throw ({_powershell_text(message)})"
        if shell is Shell.POWERSHELL
        else _BASH_STOP.format(text=_bash_text(message))
    )
    return "".join(f"# {line}\n" for line in lines) + stop + "\n"


def _powershell_text(text: str) -> str:
    """Write a PowerShell expression of the text, using ASCII only.

    Args:
        text: Any text.

    Returns:
        Single-quoted runs joined by `[char]::ConvertFromUtf32(…)` for the others.
    """
    parts: list[str] = []
    run: list[str] = []
    for character in text:
        if ord(character) <= _LAST_ASCII:
            run.append("''" if character == "'" else character)
            continue
        if run:
            parts.append("'" + "".join(run) + "'")
            run = []
        parts.append(f"[char]::ConvertFromUtf32(0x{ord(character):X})")
    if run or not parts:
        parts.append("'" + "".join(run) + "'")
    return " + ".join(parts)


def _bash_text(text: str) -> str:
    """Quote the text for bash.

    Args:
        text: Any text.

    Returns:
        The text between single quotes, its own quotes escaped.
    """
    return "'" + text.replace("'", "'\\''") + "'"
