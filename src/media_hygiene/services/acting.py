"""The guards of every command that changes files: `clean`, `sort`, `undo`.

Nothing changes unless every change can be journaled on a persistent `/journal`, and the
folders to change are not mounted read-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_read_only
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def ensure_can_act(runtime: Runtime, command: str) -> None:
    """Refuse to change anything without a journal, or on read-only folders.

    Args:
        runtime: Settings, mount points and output.
        command: The command about to act, as the user typed it.

    Raises:
        MountError: The journal is not persistent, a folder is read-only, or the
            journal or the quarantine is not writable.
    """
    if not runtime.persistent(MountKind.JOURNAL):
        raise MountError(
            _("No journal mount: without a journal, 'undo' would be impossible."),
            _('Add -v "<a folder of yours>:/journal" to the docker run command.'),
        )
    read_only = [
        root
        for root in runtime.mounts.data_roots(runtime.locations.data_dir)
        if root.is_dir() and is_read_only(root)
    ]
    if read_only:
        folders = ", ".join(runtime.mapper.to_host(root) for root in read_only)
        raise MountError(
            _("These folders are mounted read-only: {folders}.").format(
                folders=folders
            ),
            _("Remove ':ro' from their -v options to let '{command}' act.").format(
                command=command
            ),
        )
    ensure_writable(runtime, MountKind.JOURNAL, MountKind.QUARANTINE)
