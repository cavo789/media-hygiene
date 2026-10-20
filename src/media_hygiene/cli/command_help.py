"""The commands as `--help` lists them: name, panel and one-line help each."""

from __future__ import annotations

from media_hygiene.cli.command_table import command_table
from media_hygiene.i18n import _


def command_help() -> tuple[tuple[str, str, str], ...]:
    """List the commands in the order of `--help`, their help translated.

    The read-only panel comes first, then the actions; each one sorted by name.

    Returns:
        Name, panel and help text of each command.
    """
    analyse = _("🔒 Analyse: read-only, never changes your photos")
    act = _("Act: moves, writes or deletes files")
    panels = (analyse, act)
    return tuple(
        sorted(
            command_table(analyse, act),
            key=lambda command: (panels.index(command[1]), command[0]),
        )
    )
