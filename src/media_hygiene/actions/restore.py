"""Carry out the reversal of one action: the content comes back identical, or not."""

from __future__ import annotations

import errno
import os
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.link_undo import separate
from media_hygiene.actions.no_overwrite import (
    copy_exclusive,
    create_empty,
    move_no_replace,
)
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.actions.reversal import XMP_REVERSALS, Reversal, source_of
from media_hygiene.actions.xmp_undo import undo_xmp
from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry

# Undone in place: a sidecar `xmp` wrote, a mark, a copy made a link (0213).
_IN_PLACE: Final = XMP_REVERSALS | {Reversal.FORGET_MARK, Reversal.SEPARATE_LINK}
# A name an album run made: a link (its file keeps its other names), the marker;
# a copy `import` made, proven unchanged by `blocker` (0245).
_REMOVALS: Final = frozenset(
    {Reversal.REMOVE_LINK, Reversal.REMOVE_MARKER, Reversal.REMOVE_COPY}
)


def perform(entry: JournalEntry, reversal: Reversal) -> None:
    """Undo an action that `blocker` allowed.

    Nothing is ever replaced: a file that appeared where the content comes back since
    `blocker` looked stops the reversal (the content stays where it is).

    Args:
        entry: The action.
        reversal: How it is undone.

    Raises:
        OSError: The file could not be restored identical, or something is in its
            place already (nothing is left half done).
    """
    path = Path(entry.path)
    if _without_a_file(entry, reversal):
        return
    if reversal is Reversal.REMOVE_CREATED_FOLDER:
        path.rmdir()  # an empty folder only: rmdir refuses any other
        return
    if reversal in _REMOVALS:
        path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if reversal is Reversal.RECREATE_FOLDER:
        path.mkdir()
        return
    try:
        _bring_back(entry, reversal)
    except FileExistsError:
        raise FileExistsError(
            errno.EEXIST, _("it already exists"), entry.host_path
        ) from None
    relinked = reversal is Reversal.RELINK  # the photo's own time: never changed
    if not relinked and path.stat().st_mtime_ns != entry.mtime_ns:  # a move kept it
        # Only the owner may set a time: not the image's user on a file it did not make.
        os.utime(path, ns=(entry.mtime_ns, entry.mtime_ns))


def _without_a_file(entry: JournalEntry, reversal: Reversal) -> bool:
    """Undo in place: a sidecar `xmp` wrote, a mark (0224), a copy made a link (0213).

    Args:
        entry: The action.
        reversal: How it is undone.

    Returns:
        True when it is undone (a mark: the undo line in the journal is the change).
    """
    if reversal in XMP_REVERSALS:
        undo_xmp(entry)
    if reversal is Reversal.SEPARATE_LINK:
        separate(entry)  # the name stays: it becomes its own file again (0213)
    return reversal in _IN_PLACE


def _bring_back(entry: JournalEntry, reversal: Reversal) -> None:
    """Put the content of a file back in place, never over another file.

    Args:
        entry: The action.
        reversal: How it is undone: from a source, or an empty file.
    """
    path = Path(entry.path)
    source = source_of(entry, reversal)
    if source is None:
        create_empty(path)
    elif reversal is Reversal.MOVE_BACK:
        move_no_replace(source, path)
    elif reversal is Reversal.RELINK:  # an album's name of the same photo (0374)
        os.link(source, path)
    elif entry.action in QUARANTINED:
        _unquarantine(entry, source)
    else:
        _copy_back(entry, source)


def _unquarantine(entry: JournalEntry, source: Path) -> None:
    """Move a quarantined file back, once proven to be the file set aside.

    Args:
        entry: The action.
        source: The quarantined copy.

    Raises:
        OSError: The quarantined copy is not the file set aside (it stays there).
    """
    if entry.sha256 is not None and full_digest(source) != entry.sha256:
        raise OSError(_("the restored copy does not match the original"))
    move_no_replace(source, Path(entry.path))


def _copy_back(entry: JournalEntry, source: Path) -> None:
    """Rebuild a deleted copy from the kept one, proven identical.

    Args:
        entry: The action.
        source: The kept copy (it stays).

    Raises:
        OSError: The rebuilt content does not match the journaled digest (the
            rebuilt file, created here, is removed).
    """
    path = Path(entry.path)
    copy_exclusive(source, path)
    if entry.sha256 is not None and full_digest(path) != entry.sha256:
        path.unlink()
        raise OSError(_("the restored copy does not match the original"))
