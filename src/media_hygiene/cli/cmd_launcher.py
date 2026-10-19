"""`media-hygiene launcher`: write `mh`, a function holding the mounts of this run."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Annotated, NoReturn

import typer

from media_hygiene.cli.cmd_launcher_parts import backup_option
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.constants import ExitCode
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import Shell

if TYPE_CHECKING:
    from media_hygiene.services.launcher import LauncherScript
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
    backup: Annotated[list[str] | None, backup_option()] = None,
) -> None:
    """Print the script of the `mh` function; every message goes to stderr.

    Args:
        ctx: Typer context holding the runtime.
        shell: `--shell`, None to guess it.
        photos: `--photos`, the photo folders typed.
        quarantine: `--quarantine`, the quarantine folder typed.
        backup: `--backup`, the backup folders typed, always read-only (0205).
    """
    from media_hygiene.console.output import data_on_terminal
    from media_hygiene.services.launcher import render_script
    from media_hygiene.services.launcher_file import written
    from media_hygiene.services.launcher_folders import FolderChoice
    from media_hygiene.services.launcher_memory import remembered

    runtime = runtime_of(ctx)
    choice = FolderChoice(tuple(photos or ()), quarantine, tuple(backup or ()))
    script = _built(ctx, shell, choice)
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
    if done := written(script.shell):
        runtime.output.success(done)


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
    from media_hygiene.cli.cmd_launcher_parts import cli_commands
    from media_hygiene.services.launcher import launcher_script
    from media_hygiene.services.launcher_backups import with_backups
    from media_hygiene.services.launcher_folders import with_folders

    runtime = runtime_of(ctx)
    shell = shell or choice.shell()
    try:
        script = launcher_script(runtime, shell, cli_commands(ctx))
        script = with_folders(runtime, script, choice)
        return with_backups(runtime, script, choice.backups)
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
