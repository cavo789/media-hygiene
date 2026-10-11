"""A missing tool folder, reported with the full command that mounts it.

`-v "<a folder of yours>:/config"` asks the user to rebuild a `docker run` by hand; the
error carries instead this run's command again, the missing folders added in the home.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.services.next_command import next_command

if TYPE_CHECKING:
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
