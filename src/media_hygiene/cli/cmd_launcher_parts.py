"""What `launcher` reads of the CLI: its commands, and its `--backup` option (0205).

Apart from `cmd_launcher.py`, which holds the command; imports lazy, as a command's.
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import TYPE_CHECKING, Final, cast

import typer

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typer.models import OptionInfo

    from media_hygiene.services.launcher import LauncherCommands

_BACKUP: Final = "--backup"


def backup_option() -> OptionInfo:
    """`launcher --backup`: a backup folder, mounted read-only for every command.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            _BACKUP,
            help=_(
                'A backup or an old disk, as Explorer shows it: "E:\\Backup". Mounted '
                "read-only for every command, clean included, and given as --backup: "
                "compared, never changed. Repeatable."
            ),
            show_default=False,
        ),
    )


def cli_commands(ctx: typer.Context) -> LauncherCommands:
    """List the commands of the CLI, and which ones change the photos.

    Args:
        ctx: Typer context of the running command.

    Returns:
        The commands, the photos read-write for those not read-only.
    """
    from typer.core import TyperGroup

    from media_hygiene.cli.context import runtime_of
    from media_hygiene.cli.safety import (
        DATA_COMMANDS,
        LONG_COMMANDS,
        PAGE_COMMANDS,
        READ_ONLY_COMMANDS,
    )
    from media_hygiene.services.launcher import LauncherCommands

    root = ctx.find_root()
    group = root.command
    if not isinstance(group, TyperGroup):
        group = TyperGroup()
    names = tuple(group.list_commands(root))
    return LauncherCommands(
        names=names,
        writers=tuple(name for name in names if name not in READ_ONLY_COMMANDS),
        pages=tuple(name for name in names if name in PAGE_COMMANDS),
        data=tuple(name for name in names if name in DATA_COMMANDS),
        long=tuple(name for name in names if name in LONG_COMMANDS),
        port=runtime_of(ctx).settings.review.port,
        backups=tuple(
            name for name in names if _takes_backup(group.get_command(root, name))
        ),
    )


def _takes_backup(command: object) -> bool:
    """Tell whether a command has the `--backup` option (0204).

    Args:
        command: A command of the CLI (a click command), None when not found.

    Returns:
        True when it takes backup folders.
    """
    params = getattr(command, "params", ())
    return any(_BACKUP in getattr(param, "opts", ()) for param in params)
