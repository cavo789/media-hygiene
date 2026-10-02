"""Carry out the reversal of one action: the content comes back identical, or not."""

from __future__ import annotations

import errno
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.quarantine import QUARANTINED, move_verified
from media_hygiene.actions.reversal import Reversal, source_of
from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry

# A name an album run made: a link (its file keeps its other names), the marker.
_REMOVALS: Final = frozenset({Reversal.REMOVE_LINK, Reversal.REMOVE_MARKER})


def perform(entry: JournalEntry, reversal: Reversal) -> None:
    """Undo an action that `blocker` allowed.

    Args:
        entry: The action.
        reversal: How it is undone.

    Raises:
        OSError: The file could not be restored identical (nothing is left half done).
    """
    path = Path(entry.path)
    if reversal is Reversal.REMOVE_CREATED_FOLDER:
        path.rmdir()
        return
    if reversal in _REMOVALS:
        path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if reversal is Reversal.RECREATE_FOLDER:
        path.mkdir()
        return
    source = source_of(entry, reversal)
    if source is None:
        path.touch()
    elif reversal is Reversal.MOVE_BACK:
        _move(source, path)
    else:
        _copy_back(entry, source)
    os.utime(path, ns=(entry.mtime_ns, entry.mtime_ns))


def _move(source: Path, destination: Path) -> None:
    """Move a file back: renamed on the same disk, copied and verified across disks.

    Args:
        source: Where it is.
        destination: Where it was.
    """
    try:
        source.rename(destination)
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise
        move_verified(source, destination)


def _copy_back(entry: JournalEntry, source: Path) -> None:
    """Rebuild a file from a copy, prove it identical, release the quarantined copy.

    Args:
        entry: The action.
        source: The kept or quarantined copy.

    Raises:
        OSError: The rebuilt content does not match the journaled digest.
    """
    path = Path(entry.path)
    shutil.copy2(source, path)
    if entry.sha256 is not None and full_digest(path) != entry.sha256:
        path.unlink()
        raise OSError(_("the restored copy does not match the original"))
    if entry.action in QUARANTINED:
        source.unlink()
