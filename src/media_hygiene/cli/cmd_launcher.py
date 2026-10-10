"""`media-hygiene launcher`: write `mh`, a function holding the mounts of this run."""

from __future__ import annotations

import sys
from typing import Annotated

import typer
from typer.core import TyperGroup

from media_hygiene.cli.context import runtime_of
from media_hygiene.cli.review_options import PAGE_PORT
from media_hygiene.cli.safety import (
    DATA_COMMANDS,
    PAGE_COMMANDS,
    READ_ONLY_COMMANDS,
)
from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import Shell
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    load_command,
    render_script,
)


def launcher_command(
    ctx: typer.Context,
    shell: Annotated[
        Shell | None,
        typer.Option(
            "--shell",
            help=_(
                "The shell of the script: 'powershell' (Windows) or 'bash' (WSL, "
                "Linux, macOS). Default: guessed from the mounted folders."
            ),
            show_default=False,
        ),
    ] = None,
) -> None:
    """Print the script of the `mh` function; every message goes to stderr.

    Args:
        ctx: Typer context holding the runtime.
        shell: `--shell`, None to guess it.
    """
    runtime = runtime_of(ctx)
    script = launcher_script(runtime, shell, _commands(ctx))
    sys.stdout.write(render_script(script))
    sys.stdout.flush()
    if not script.data:
        runtime.output.warning(
            _("No photo folder mounted: add -v for each folder, then run it again.")
        )
    runtime.output.success(
        _("Launcher written. Load it with: {load}, then type: mh audit").format(
            load=load_command(script.shell)
        )
    )


def _commands(ctx: typer.Context) -> LauncherCommands:
    """List the commands of the CLI, and which ones change the photos.

    Args:
        ctx: Typer context of the running command.

    Returns:
        The commands, the photos read-write for those not read-only.
    """
    root = ctx.find_root()
    group = root.command
    names = tuple(group.list_commands(root)) if isinstance(group, TyperGroup) else ()
    return LauncherCommands(
        names=names,
        writers=tuple(name for name in names if name not in READ_ONLY_COMMANDS),
        pages=tuple(name for name in names if name in PAGE_COMMANDS),
        data=tuple(name for name in names if name in DATA_COMMANDS),
        port=PAGE_PORT,
    )
