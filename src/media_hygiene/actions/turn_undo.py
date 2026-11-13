"""Undo a turn: the old orientation code and time back, proven byte-identical (0802).

A photo is only touched while it still holds, byte for byte, what the run wrote (the
journal keeps its SHA-256): one edited since is kept, and the reason told. The old
code written back must give the SHA-256 the journal kept before the turn, or nothing
is written.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import Status
from media_hygiene.actions.orientation_bytes import with_orientation
from media_hygiene.actions.turn_write import put_bytes
from media_hygiene.actions.xmp_undo import holds_ours
from media_hygiene.actions.xmp_write import digest
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry


def never_turned(entry: JournalEntry) -> bool:
    """Tell whether a run stopped before this photo was turned.

    Args:
        entry: The turn, maybe `pending`.

    Returns:
        True for a `pending` turn whose bytes are not there: nothing to undo.
    """
    return entry.status is Status.PENDING and not holds_ours(entry)


def turn_blocker(entry: JournalEntry) -> str | None:
    """Tell why a turn cannot be undone right now.

    Args:
        entry: The turn.

    Returns:
        The translated reason, or None when it can be undone.
    """
    if not Path(entry.path).is_file():
        return _("it is no longer there: moved or deleted since")
    if entry.orientation is None:
        return _("the journal does not say what the photo held before")
    if not holds_ours(entry):
        return _("the photo changed since (edited in another application?): kept")
    return None


def undo_turn(entry: JournalEntry) -> None:
    """Write the old orientation code back, then the old modification time.

    Args:
        entry: The turn `turn_blocker` allowed.

    Raises:
        OSError: The old code does not give the bytes held before the turn.
    """
    path = Path(entry.path)
    code, before = entry.orientation or (0, "")
    now = path.read_bytes()
    restored, _code = with_orientation(now, code)
    if digest(restored) != before:
        raise OSError(_("the photo would not be the same as before: kept"))
    put_bytes(path, restored, now)
    os.utime(path, ns=(entry.mtime_ns, entry.mtime_ns))
