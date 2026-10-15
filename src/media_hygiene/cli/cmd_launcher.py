"""`media-hygiene launcher`: write `mh`, a function holding the mounts of this run."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Annotated, NoReturn

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.review_options import PAGE_PORT
from media_hygiene.constants import ExitCode
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import Shell

if TYPE_CHECKING:
    from media_hygiene.services.launcher import LauncherCommands, LauncherScript
    from media_hygiene.services.launcher_folders import FolderChoice
    from media_hygiene.services.runtime import Runtime


def launcher_command(  # pylint: disable=too-many-arguments  # one per option
    ctx: typer.Context,
    *,
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
    photos: Annotated[
        list[str] | None,
        typer.Option(
            "--photos",
            help=_(
                "A folder of photos and videos, as Explorer shows it: "
                '"C:\\Photos" (or /mnt/c/Photos in WSL). Repeat it for several '
                "folders. No -v needed."
            ),
            show_default=False,
        ),
    ] = None,
    quarantine: Annotated[
        str | None,
        typer.Option(
            "--quarantine",
            help=_(
                "Where the copies set aside go, once: best on the photos' disk "
                "(a move, not a copy). Default: the quarantine folder of your home."
            ),
            show_default=False,
        ),
    ] = None,
) -> None:
    """Print the script of the `mh` function; every message goes to stderr.

    Args:
        ctx: Typer context holding the runtime.
        shell: `--shell`, None to guess it.
        photos: `--photos`, the photo folders typed.
        quarantine: `--quarantine`, the quarantine folder typed.
    """
    from media_hygiene.console.output import data_on_terminal
    from media_hygiene.services.launcher import load_command, render_script
    from media_hygiene.services.launcher_folders import FolderChoice
    from media_hygiene.services.launcher_memory import remembered

    runtime = runtime_of(ctx)
    script = _built(ctx, shell, FolderChoice(tuple(photos or ()), quarantine))
    if data_on_terminal():
        _refuse_terminal(script.shell)
    sys.stdout.write(render_script(script))
    sys.stdout.flush()
    if not script.data:
        runtime.output.warning(
            _(
                'No photo folder: add --photos "C:\\Photos" for each folder, then run '
                "it again."
            )
        )
    runtime.output.info(remembered(runtime, script))
    runtime.output.success(
        _("Launcher written. Load it with: {load}, then type: mh audit").format(
            load=load_command(script.shell)
        )
    )


def _built(
    ctx: typer.Context, shell: Shell | None, choice: FolderChoice
) -> LauncherScript:
    """Build the script from the mounts of this run and the folders typed.

    Args:
        ctx: Typer context holding the runtime.
        shell: `--shell`, None to guess it from the folders.
        choice: The folders of `--photos` and `--quarantine`.

    Returns:
        The script.
    """
    from media_hygiene.services.launcher import launcher_script
    from media_hygiene.services.launcher_folders import with_folders

    runtime = runtime_of(ctx)
    shell = shell or choice.shell()
    try:
        return with_folders(
            runtime, launcher_script(runtime, shell, _commands(ctx)), choice
        )
    except MountError as error:
        _refuse_folder(runtime, shell or Shell.POWERSHELL, error)


def _refuse_terminal(shell: Shell) -> None:
    """Stop when the script would land on the screen instead of in a file.

    `-t` joins stderr to stdout: a redirection catches the refusal too, so it is
    written as a script that stops its own loading with the same advice.

    Args:
        shell: The shell the script is for.

    Raises:
        typer.Exit: Always: no launcher was written.
    """
    from media_hygiene.services.launcher_refusal import refusal_script

    sys.stdout.write(refusal_script(shell))
    sys.stdout.flush()
    raise typer.Exit(ExitCode.USAGE)


def _refuse_folder(runtime: Runtime, shell: Shell, error: MountError) -> NoReturn:
    """Stop on a folder that cannot be mounted: said on screen and in the script.

    `> mh.ps1` empties the file anyway: what lands in it stops its own loading with
    the same advice, rather than leaving an empty `mh`.

    Args:
        runtime: Settings, mount points and output.
        shell: The shell the script is for.
        error: Why the folder is refused.

    Raises:
        MountError: Always, reported by the usual error handler.
    """
    from media_hygiene.services.launcher_refusal import stopping_script

    lines = (error.message, *((error.tip,) if error.tip else ()))
    sys.stdout.write(stopping_script(shell, lines))
    sys.stdout.flush()
    with user_errors(runtime.output):
        raise error


def _commands(ctx: typer.Context) -> LauncherCommands:
    """List the commands of the CLI, and which ones change the photos.

    Args:
        ctx: Typer context of the running command.

    Returns:
        The commands, the photos read-write for those not read-only.
    """
    from typer.core import TyperGroup

    from media_hygiene.cli.safety import (
        DATA_COMMANDS,
        PAGE_COMMANDS,
        READ_ONLY_COMMANDS,
    )
    from media_hygiene.services.launcher import LauncherCommands

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
