"""A missing tool folder, reported with the full command that mounts it.

`-v "<a folder of yours>:/config"` asks the user to rebuild a `docker run` by hand; the
error carries instead this run's command again, the missing folders added in the home.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.services.next_command import next_command

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.services.next_command import NextVerb
    from media_hygiene.services.runtime import Runtime


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
