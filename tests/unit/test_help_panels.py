"""Help in panels: read-only commands apart, daily options before "Advanced" ones."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest
import typer.main
from typer.core import TyperOption

from media_hygiene.cli.app import build_app
from media_hygiene.cli.options import panel_local_ai
from media_hygiene.cli.safety import READ_ONLY_COMMANDS, read_only_marker

if TYPE_CHECKING:
    from typer._click import Command

# More options than this, and the help splits them into two panels.
_FEW_OPTIONS: Final = 4

_DAILY: Final = {
    "clean": {"--tier", "--decisions", "--yes"},
    "review": {"--near", "--pairs", "--junk"},
    "classify": {"--year", "--path", "--layout", "--target"},
    "album": {"--category", "--event", "--apply"},
    "audit": set(),
    "crosscheck": set(),
}

# The options that only serve a local vision model, and the commands that have them.
_LOCAL_AI: Final = {"--sample", "--no-describe", "--yes"}
_WITH_LOCAL_AI: Final = ("tags", "classify")


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
    """The options of daily use stay in Typer's first panel; no other does.

    Args:
        name: The command.
        daily: Its options of daily use.
    """
    options = _options(name)
    assert len(options) > _FEW_OPTIONS
    unpanelled = {option.opts[0] for option in options if not option.rich_help_panel}
    assert unpanelled == daily


def test_few_options_keep_one_panel() -> None:
    """`--port` stays in the first panel of commands with few options."""
    assert [option.rich_help_panel for option in _options("places")] == [None]


def test_read_only_commands_share_one_panel_sorted_by_name() -> None:
    """Read-only commands first, then the others; each panel in alphabetical order."""
    infos = build_app().registered_commands
    names = [info.name or "" for info in infos]
    read_only = names[: len(READ_ONLY_COMMANDS)]
    assert set(read_only) == READ_ONLY_COMMANDS
    assert read_only == sorted(read_only)
    assert names[len(read_only) :] == sorted(names[len(read_only) :])
    assert len({info.rich_help_panel for info in infos}) == len(("read-only", "act"))


def test_command_list_does_not_repeat_the_read_only_marker() -> None:
    """The panel title says it once; each command's own help still opens with it."""
    for info in build_app().registered_commands:
        assert not (info.short_help or "").startswith(read_only_marker())
        marked = (info.help or "").startswith(read_only_marker())
        assert marked == (info.name in READ_ONLY_COMMANDS)


@pytest.mark.parametrize("name", _WITH_LOCAL_AI)
def test_local_ai_options_stand_apart(name: str) -> None:
    """What needs Ollama shows at a glance: its own 🤖 panel, and 🤖 in the list.

    The robot ends the command's line: a word after it can make Rich cut the line.

    Args:
        name: The command.
    """
    panelled = {
        option.opts[0]
        for option in _options(name)
        if option.rich_help_panel == panel_local_ai()
    }
    assert panelled == _LOCAL_AI
    info = next(info for info in build_app().registered_commands if info.name == name)
    assert (info.short_help or "").endswith("🤖")
