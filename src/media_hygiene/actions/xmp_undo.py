"""Undo the sidecars of an `xmp` run: remove ours, put the others back as they were.

A sidecar is only touched when it still holds, byte for byte, what the run wrote (the
journal keeps its SHA-256): one edited since in another application is kept, and the
reason told. A sidecar this tool created is removed; one it rewrote gets its previous
bytes back from the quarantine, atomically.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import ActionKind, Status
from media_hygiene.actions.xmp_write import digest
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry

_TEMPORARY: Final = ".media-hygiene.undo"


def holds_ours(entry: JournalEntry) -> bool:
    """Tell whether the sidecar still holds what the run wrote.

    Args:
        entry: The write.

    Returns:
        True when its bytes have the journaled SHA-256.
    """
    path = Path(entry.path)
    try:
        return entry.sha256 is not None and digest(path.read_bytes()) == entry.sha256
    except OSError:
        return False


def never_written(entry: JournalEntry) -> bool:
    """Tell whether a run stopped before this sidecar was written.

    Args:
        entry: The write, maybe `pending`.

    Returns:
        True for a `pending` write whose content is not there: nothing to undo.
    """
    return entry.status is Status.PENDING and not holds_ours(entry)


def xmp_blocker(entry: JournalEntry) -> str | None:
    """Tell why a sidecar cannot be undone right now.

    Args:
        entry: The write.

    Returns:
        The translated reason, or None when it can be undone.
    """
    if not Path(entry.path).is_file():
        return _("the sidecar is gone already")
    if not holds_ours(entry):
        return _("the sidecar changed since (edited in another application?): kept")
    if entry.action is ActionKind.CREATE_XMP:
        return None
    backup = Path(entry.quarantine) if entry.quarantine else None
    if backup is None or not backup.is_file():
        return _("its previous content is no longer in the quarantine: kept")
    return None


def undo_xmp(entry: JournalEntry) -> None:
    """Remove a sidecar the run created, or put the previous one back.

    Args:
        entry: The write `xmp_blocker` allowed.
    """
    path = Path(entry.path)
    if entry.action is ActionKind.CREATE_XMP or not entry.quarantine:
        path.unlink()
        return
    previous = Path(entry.quarantine).read_bytes()
    temporary = path.with_name(path.name + _TEMPORARY)
    with temporary.open("wb") as stream:
        stream.write(previous)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
