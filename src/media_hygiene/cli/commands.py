"""The commands of the CLI: name, function, help panel and one-line help each."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.command_functions import command_functions
from media_hygiene.cli.command_help import command_help

if TYPE_CHECKING:
    from collections.abc import Callable


def commands() -> tuple[tuple[str, Callable[..., None], str, str], ...]:
    """List the commands in the order of `--help`, their help translated.

    Returns:
        Name, function, panel and help text of each command.
    """
    functions = command_functions()
    return tuple(
        (name, functions[name], panel, text) for name, panel, text in command_help()
    )
