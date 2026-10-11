"""Help in two panels: daily options first, the others under "Advanced"."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest
import typer.main
from typer.core import TyperOption

from media_hygiene.cli.app import build_app

if TYPE_CHECKING:
    from typer._click import Command

# More options than this, and the help splits them into two panels.
_FEW_OPTIONS: Final = 4

_DAILY: Final = {
    "clean": {"--tier", "--decisions", "--yes"},
    "review": {"--near"},
    "classify": {"--year", "--layout", "--target"},
    "album": {"--category", "--event", "--apply"},
    "audit": set(),
    "crosscheck": set(),
}


def _options(name: str) -> list[TyperOption]:
    """The options of one command, `--help` left out.

    Args:
        name: The command.

    Returns:
        Its options, in the order the help lists them.
    """
    group = typer.main.get_command(build_app())
    command: Command = group.commands[name]  # type: ignore[attr-defined]
    return [param for param in command.params if isinstance(param, TyperOption)]


@pytest.mark.parametrize(("name", "daily"), _DAILY.items())
def test_daily_options_come_first_without_panel(name: str, daily: set[str]) -> None:
    """The options of daily use stay in Typer's first panel; no other does."""
    options = _options(name)
    assert len(options) > _FEW_OPTIONS
    unpanelled = {option.opts[0] for option in options if not option.rich_help_panel}
    assert unpanelled == daily


def test_few_options_keep_one_panel() -> None:
    """`--port` stays in the first panel of commands with few options."""
    assert [option.rich_help_panel for option in _options("places")] == [None]
