"""A thin, typed facade over Rich for consistent, coloured and translated messages."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markup import escape
from rich.style import Style
from rich.text import Text

from media_hygiene.console.advice import Advice, AdviceBoard, TipKind
from media_hygiene.console.advice_view import print_advice
from media_hygiene.constants import ColorMode
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from rich.console import RenderableType

_YES_ANSWERS = frozenset({"y", "yes"})


def make_console(color: ColorMode, *, stderr: bool = False) -> Console:
    """Create the Rich console for a colour mode (`NO_COLOR` is honoured by Rich).

    Args:
        color: `auto` detects a terminal, `always`/`never` force the choice.
        stderr: Print to the error stream, keeping the output stream for data
            redirected to a file (the `launcher` script). When the output stream is
            a terminal, the console is silent: under `docker run -t` both streams
            are one, and `> file` would catch the messages along with the data.

    Returns:
        The console.
    """
    quiet = stderr and data_on_terminal()
    match color:
        case ColorMode.ALWAYS:
            return Console(
                force_terminal=True, highlight=False, stderr=stderr, quiet=quiet
            )
        case ColorMode.NEVER:
            return Console(no_color=True, highlight=False, stderr=stderr, quiet=quiet)
        case ColorMode.AUTO:
            return Console(highlight=False, stderr=stderr, quiet=quiet)


def data_on_terminal() -> bool:
    """Whether the output stream is a terminal rather than a file (`docker run -t`).

    Returns:
        True when data written to stdout would land on the screen.
    """
    return sys.stdout.isatty()


@dataclass(frozen=True, slots=True)
class Output:
    """Semantic output channel: every message kind has its own style and emoji.

    `tip()` prints at once (a tip about what is on screen); `advise()`, `setting()`
    and `next_step()` collect the closing advice, printed by `finish()` at the end
    of the command, ranked and cut to a budget unless `verbose`.
    """

    console: Console
    verbose: bool = False
    board: AdviceBoard = field(default_factory=AdviceBoard)

    def title(self, text: str) -> None:
        """Print a section title.

        Args:
            text: Translated title.
        """
        self.console.rule(f"[bold blue]{text}[/]")

    def info(self, text: str) -> None:
        """Print an informational line.

        Args:
            text: Translated message.
        """
        self.console.print(text)

    def success(self, text: str) -> None:
        """Print a success line.

        Args:
            text: Translated message.
        """
        self.console.print(f"✅ [green]{text}[/]")

    def warning(self, text: str) -> None:
        """Print a warning line.

        Args:
            text: Translated message.
        """
        self.console.print(f"⚠️  [yellow]{text}[/]")

    def error(self, text: str) -> None:
        """Print an error line.

        Args:
            text: Translated message.
        """
        self.console.print(f"❌ [bold red]{text}[/]")

    def tip(self, text: str) -> None:
        """Print a 💡 tip — shown as soon as there is something useful to suggest.

        Args:
            text: Translated tip.
        """
        self.console.print(f"💡 [cyan]{text}[/]")

    def advise(self, advice: Advice) -> None:
        """Collect a tip for the end of the command, where it is ranked by kind.

        Args:
            advice: The tip, its kind and the command it suggests, if any.
        """
        self.board.add(advice)

    def setting(self, fragment: str) -> None:
        """Collect an option worth setting once; all of them end up on one line.

        Args:
            fragment: Translated, e.g. `-e TZ=Europe/Brussels (local times)`.
        """
        self.board.add_setting(fragment)

    def next_step(self, text: str, command: str | None = None) -> None:
        """Set the step that logically comes next, printed first by `finish()`.

        Args:
            text: Translated step, starting in lower case after the label.
            command: The full command to paste, when the step is one.
        """
        self.board.step = Advice(TipKind.NEXT, text, command)

    def drop_advice(self) -> None:
        """Forget the advice collected: the user declined, nothing is to follow."""
        self.board.drain()

    def finish(self) -> None:
        """Print the collected advice, then an empty line before the shell prompt."""
        print_advice(self, self.board.drain())
        self.blank()

    def command(self, text: str) -> None:
        """Print a command to copy and paste, never cut by a line break.

        Args:
            text: The command, printed as is (no markup, no highlighting).
        """
        self.console.print(text, soft_wrap=True, markup=False, highlight=False)

    def link(self, label: str, url: str) -> None:
        """Print a page to open, the URL never cut by a line break (Ctrl+click).

        Args:
            label: Translated, e.g. `Step 1 of the guide:`.
            url: The page, also a terminal hyperlink where the terminal supports it.
        """
        line = Text(f"📖 {label} ")
        line.append(url, style=Style(link=url))
        self.console.print(line, soft_wrap=True, highlight=False)

    def show(self, renderable: RenderableType) -> None:
        """Print any Rich renderable (tables, panels).

        Args:
            renderable: What to print.
        """
        self.console.print(renderable)

    def blank(self) -> None:
        """Print an empty line, to let the sections breathe."""
        self.console.line()

    def confirm(self, question: str) -> bool:
        """Ask a yes/no question; anything but an explicit yes means no.

        Args:
            question: Translated question.

        Returns:
            True only for an explicit yes (in English or in the active language).
        """
        if not sys.stdin.isatty():
            return False
        # Escaped: Rich would read "[y/N]" as a style tag and print nothing.
        answer = self.console.input(f"❓ {question} [bold]{escape(_('[y/N]'))}[/] ")
        accepted = _YES_ANSWERS | {_("y"), _("yes")}
        return answer.strip().casefold() in accepted
