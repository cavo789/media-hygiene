"""The commands of the CLI: name, function, help panel and one-line help each."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.command_table import command_table
from media_hygiene.cli.safety import help_of
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable


def commands() -> tuple[tuple[str, Callable[..., None], str, str], ...]:
    """List the commands in the order of `--help`, their help translated.

    Returns:
        Name, function, panel and help text of each command.
    """
    analyse, act = _("Analyse"), _("Act")
    return tuple(
        (name, function, panel, help_of(name, text))
        for name, function, panel, text in command_table(analyse, act)
    )
