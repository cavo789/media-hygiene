"""Messages stay whole without a terminal; tables keep a width (0541)."""

from __future__ import annotations

import io
from typing import override

import pytest
from rich.console import Console
from rich.table import Table

from media_hygiene.console import one_line
from media_hygiene.console.one_line import TABLE_WIDTH, say, width_without_terminal
from media_hygiene.console.output import Output, make_console
from media_hygiene.constants import ColorMode

_LONG = " ".join(["word"] * 40)  # 199 characters


class _Screen(io.StringIO):
    """A stream that says it is a terminal."""

    @override
    def isatty(self) -> bool:
        """Answer as a terminal does.

        Returns:
            Always True.
        """
        return True


def _no_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COLUMNS", raising=False)
    monkeypatch.setattr(one_line, "_has_terminal", lambda: False)


@pytest.mark.parametrize("forced", [None, True])
@pytest.mark.parametrize("kind", ["info", "success", "warning", "error", "tip"])
def test_long_message_has_no_break(kind: str, *, forced: bool | None) -> None:
    """Even under `--color always`, which makes Rich call the stream a terminal."""
    buffer = io.StringIO()
    console = Console(file=buffer, width=80, force_terminal=forced, no_color=True)
    getattr(Output(console), kind)(_LONG)
    assert _LONG in buffer.getvalue()
    assert buffer.getvalue().count("\n") == 1


def test_what_next_has_no_break() -> None:
    """The closing line goes the same way."""
    buffer = io.StringIO()
    output = Output(Console(file=buffer, width=80))
    output.next_step(_LONG)
    output.finish()
    assert _LONG in buffer.getvalue()


def test_a_terminal_still_wraps() -> None:
    """On a screen, Rich fits the words to the window, as before."""
    screen = _Screen()
    say(Console(file=screen, width=80), _LONG)
    assert _LONG not in screen.getvalue()


def test_a_table_keeps_the_width() -> None:
    """A table is not one line: it fits the console's width."""
    buffer = io.StringIO()
    table = Table("Text")
    table.add_row(_LONG)
    say(Console(file=buffer, width=80), table)
    assert max(map(len, buffer.getvalue().splitlines())) <= 80


def test_multi_line_message_keeps_its_own_breaks() -> None:
    """Only the breaks Rich would add go."""
    buffer = io.StringIO()
    say(Console(file=buffer, width=80), f"{_LONG}\nsecond")
    assert buffer.getvalue() == f"{_LONG}\nsecond\n"


def test_width_comes_from_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    """The host's width wins; Rich reads it itself."""
    _no_terminal(monkeypatch)
    monkeypatch.setenv("COLUMNS", "150")
    assert width_without_terminal() is None
    assert make_console(ColorMode.NEVER).width == 150


@pytest.mark.parametrize("columns", [None, "", "0", "wide"])
def test_width_by_default(monkeypatch: pytest.MonkeyPatch, columns: str | None) -> None:
    """No terminal and no usable width (a window reporting 0): the default."""
    _no_terminal(monkeypatch)
    if columns is not None:
        monkeypatch.setenv("COLUMNS", columns)
    assert make_console(ColorMode.AUTO).width == TABLE_WIDTH


def test_a_terminal_gives_its_width(monkeypatch: pytest.MonkeyPatch) -> None:
    """With a terminal among the streams, nothing is imposed."""
    monkeypatch.delenv("COLUMNS", raising=False)
    monkeypatch.setattr(one_line, "_has_terminal", lambda: True)
    assert width_without_terminal() is None


@pytest.mark.parametrize(
    ("color", "is_forced"),
    [(ColorMode.ALWAYS, True), (ColorMode.NEVER, False)],
)
def test_colour_modes_are_kept(*, color: ColorMode, is_forced: bool) -> None:
    """The console built for each mode."""
    console = make_console(color)
    assert console.is_terminal is is_forced
    assert console.no_color is (not is_forced)
