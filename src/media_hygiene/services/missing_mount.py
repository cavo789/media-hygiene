"""A missing folder, reported with the full command that mounts it.

`-v "<a folder of yours>:/config"` asks the user to rebuild a `docker run` by hand; the
error carries instead this run's command again, the missing folders added (the photo
folder of the guide when there is none).
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import DOC_PAGES
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import DockerRun, Shell, Volume, guess_shell
from media_hygiene.services.next_command import (
    LAUNCHER_VARIABLE,
    TOOL_KINDS,
    environment,
    next_command,
    tool_host,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.services.next_command import NextVerb
    from media_hygiene.services.runtime import Runtime

# The example photo folder of the guide, as each shell names it, and how to check it.
_EXAMPLES: Final = {
    Shell.POWERSHELL: ("C:\\Photos", 'Test-Path "C:\\Photos"'),
    Shell.BASH: ("/mnt/c/Photos", 'ls "/mnt/c/Photos"'),
}
_EXAMPLE_POINT: Final = ("c", "Photos")  # under the data directory


def missing_mount(runtime: Runtime, message: str, again: NextVerb) -> MountError:
    """The error of a missing tool folder, with the command to run instead.

    Args:
        runtime: Settings, mount points and output.
        message: What is missing, already translated.
        again: The command to run again, `needs` naming the missing folders.

    Returns:
        The error to raise; its tip says what the command adds.
    """
    command = next_command(runtime, again)
    tip = _("Copy and paste this command to run it again.")
    note = command.note()
    error = MountError(message, f"{tip} {note}" if note else tip)
    error.command = command.command
    return error


def no_folder(runtime: Runtime, command: str) -> MountError:
    r"""The error of a run without any photo folder, with the command that mounts one.

    Args:
        runtime: Settings, mount points and output.
        command: The running command, e.g. `audit`.

    Returns:
        The error to raise, with the guide; but for the `mh` launcher (it mounts the
        folders itself), also the same run with `C:\Photos` mounted read-only, in
        PowerShell unless the tool folders of this run are Linux ones.
    """
    message = _("No folder to analyse under {path}.").format(
        path=runtime.locations.data_dir
    )
    tip = _("The tool only sees the folders you give it with -v.")
    tools = tuple(
        Volume(host, runtime.locations.path_of(kind))
        for kind in TOOL_KINDS
        if (host := tool_host(runtime, kind)) is not None
    )
    shell = guess_shell(tuple(v.host for v in tools)) if tools else Shell.POWERSHELL
    folder, check = _EXAMPLES[shell]
    error = MountError(
        message,
        tip
        if os.environ.get(LAUNCHER_VARIABLE)
        else _(
            "{tip} In this command, replace {folder} with your photo folder, after "
            "checking that it exists on your computer ({check})."
        ).format(tip=tip, folder=folder, check=check),
    )
    error.link = (
        _("Step 1 of the guide:"),
        f"{DOC_PAGES}/{_('start/01-first-audit/')}",
    )
    if not os.environ.get(LAUNCHER_VARIABLE):
        photos = Volume(
            folder, runtime.locations.data_dir.joinpath(*_EXAMPLE_POINT), read_only=True
        )
        run = DockerRun((photos, *tools), environment(), typed_again(runtime, command))
        error.command = run.render(shell)
    return error


def typed_again(runtime: Runtime, command: str) -> str:
    """The arguments the user typed for `command`, to offer the same run again.

    Args:
        runtime: Settings; its command-line layer holds the global options.
        command: The running command, e.g. `clean`.

    Returns:
        E.g. `clean --tier near`; the command and the global options alone when the
        command line is not the tool's own (tests, `python -m`).
    """
    return again_arguments(runtime, command, sys.argv[1:])


def again_arguments(runtime: Runtime, command: str, typed: Sequence[str]) -> str:
    """Quote the arguments of a command line, or rebuild the bare command.

    Args:
        runtime: Settings; its command-line layer holds the global options.
        command: The running command.
        typed: The command line, without the program name.

    Returns:
        The arguments, a value holding a space quoted.
    """
    if command not in typed:
        general = runtime.cli_layer.get("general", {})
        return " ".join(
            (*(f"--{name} {value}" for name, value in general.items()), command)
        )
    return " ".join(
        f'"{argument}"' if not argument or " " in argument else argument
        for argument in typed
    )
