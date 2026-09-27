"""Terminal captures: answer through a pseudo-terminal, tidy a screen, draw it."""

from __future__ import annotations

import io
import os
import pty
import re
import select
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from rich.ansi import AnsiDecoder
from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Sequence

_PROMPT: Final = re.compile(rb"\[[yo]/N\] $")
_RULE: Final = re.compile(r"^─+ .+ ─+$")
_READ_TIMEOUT: Final = 300.0
_CHUNK: Final = 4096
_IMAGE_WIDTH: Final = 100


@dataclass(frozen=True, slots=True)
class Window:
    """The part of a colour capture drawn as a terminal: from one line to another."""

    first: str
    last: str
    title: str


def tidy(screen: str) -> str:
    r"""Clean what a terminal showed, the way a reader sees it.

    `TERM=dumb` keeps Rich from animating progress bars, but leaves an empty line where
    each bar stood, right after the section rule: those lines go, with trailing spaces.

    Args:
        screen: The raw output, `\r\n` line endings included.

    Returns:
        The text, one line per terminal line.
    """
    lines: list[str] = []
    for line in screen.replace("\r\n", "\n").replace("\r", "").split("\n"):
        text = line.rstrip()
        if text or (lines and not _RULE.match(lines[-1])):
            lines.append(text)
    return "\n".join(lines).strip("\n") + "\n"


def answer_prompt(command: Sequence[str], answer: str) -> str:
    """Run a command in a pseudo-terminal and answer its yes/no question.

    Args:
        command: The command line, such as `docker run -it …`.
        answer: What to type at the `[y/N]` question.

    Returns:
        Everything the terminal showed, answer included.
    """
    pid, descriptor = pty.fork()
    if pid == 0:  # pragma: no cover - the child becomes the command
        os.execvp(command[0], list(command))  # noqa: S606 - fixed, trusted arguments
    screen, answered = b"", False
    while select.select([descriptor], [], [], _READ_TIMEOUT)[0]:
        try:
            chunk = os.read(descriptor, _CHUNK)
        except OSError:  # the command ended and closed the terminal
            break
        if not chunk:
            break
        screen += chunk
        if not answered and _PROMPT.search(screen):
            os.write(descriptor, f"{answer}\r".encode())
            answered = True
    os.waitpid(pid, 0)
    return screen.decode("utf-8", errors="replace")


def draw_terminal(ansi: str, window: Window) -> str:
    """Draw part of a colour capture as a terminal window (SVG), its first line on top.

    Args:
        ansi: The output of a `--color always` run, escape codes included.
        window: The lines to keep and the title of the window.

    Returns:
        The SVG document.
    """
    lines = list(AnsiDecoder().decode(ansi))
    plain = [line.plain for line in lines]
    first = next(
        index for index, text in enumerate(plain) if text.startswith(window.first)
    )
    last = next(index for index, text in enumerate(plain) if window.last in text)
    console = Console(
        record=True, width=_IMAGE_WIDTH, file=io.StringIO(), color_system="truecolor"
    )
    for line in [lines[0], *lines[first : last + 1]]:
        console.print(line, no_wrap=True, crop=True)
    return console.export_svg(title=window.title)
