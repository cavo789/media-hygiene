"""The commands of the CLI: name, function, help panel and one-line help each."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.command_table import command_table
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable


def commands() -> tuple[tuple[str, Callable[..., None], str, str], ...]:
    """List the commands in the order of `--help`, their help translated.

    The read-only panel comes first, then the actions; each one sorted by name.

    Returns:
        Name, function, panel and help text of each command.
    """
    analyse = _("🔒 Analyse: read-only, never changes your photos")
    act = _("Act: moves, writes or deletes files")
    panels = (analyse, act)
    return tuple(
        sorted(
            command_table(analyse, act),
            key=lambda command: (panels.index(command[2]), command[0]),
        )
    )
