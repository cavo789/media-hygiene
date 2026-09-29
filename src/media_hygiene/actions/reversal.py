"""How `undo` reverses each kind of action: every kind is listed, nothing is guessed.

A kind missing from `REVERSALS` stops `undo` before it changes anything: recreating an
empty file for an action it does not understand would leave a 0-byte "restored" file
while the real one lies elsewhere.
"""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.errors import JournalError
from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.actions.journal import JournalEntry


class Reversal(Enum):
    """What undoing an action means."""

    RECREATE_EMPTY = auto()
    COPY_FROM_KEEPER = auto()
    UNQUARANTINE = auto()
    MOVE_BACK = auto()
    RECREATE_FOLDER = auto()
    REMOVE_CREATED_FOLDER = auto()


REVERSALS: Final[Mapping[ActionKind, Reversal]] = MappingProxyType(
    {
        ActionKind.DELETE_EMPTY: Reversal.RECREATE_EMPTY,
        ActionKind.DELETE_DUPLICATE: Reversal.COPY_FROM_KEEPER,
        ActionKind.MOVE: Reversal.MOVE_BACK,
        ActionKind.REMOVE_FOLDER: Reversal.RECREATE_FOLDER,
        ActionKind.CREATE_FOLDER: Reversal.REMOVE_CREATED_FOLDER,
    }
    | dict.fromkeys(QUARANTINED, Reversal.UNQUARANTINE)
)
_WITHOUT_SOURCE: Final = frozenset({Reversal.RECREATE_EMPTY, Reversal.RECREATE_FOLDER})


def reversal_of(entry: JournalEntry) -> Reversal:
    """Tell how to undo an action.

    Args:
        entry: A journaled action.

    Returns:
        Its reversal.

    Raises:
        JournalError: This version does not know how to undo it.
    """
    reversal = REVERSALS.get(entry.action)
    if reversal is None:
        message = _("{path}: this version cannot undo the action '{action}'.")
        raise JournalError(
            message.format(path=entry.host_path, action=entry.action.value),
            _("Nothing was changed. Update media-hygiene, then undo this run again."),
        )
    return reversal


def blocker(entry: JournalEntry, reversal: Reversal) -> str | None:
    """Tell why an action cannot be undone right now.

    Args:
        entry: The action.
        reversal: How it is undone.

    Returns:
        The translated reason, or None when it can be undone.
    """
    path = Path(entry.path)
    if reversal is Reversal.REMOVE_CREATED_FOLDER:
        return _folder_blocker(path)
    if path.exists():
        # Never overwrite: it is back already, or the action never happened.
        return _("it already exists")
    if reversal in _WITHOUT_SOURCE:
        return None
    return _source_blocker(entry, reversal)


def _folder_blocker(folder: Path) -> str | None:
    """Tell why a folder a run created cannot be removed.

    Args:
        folder: The folder.

    Returns:
        The reason, or None when it is there and empty.
    """
    if not folder.is_dir():
        return _("the folder is gone already")
    return _("the folder is not empty") if any(folder.iterdir()) else None


def _source_blocker(entry: JournalEntry, reversal: Reversal) -> str | None:
    """Tell why the content of a file cannot come back.

    Args:
        entry: The action.
        reversal: A reversal that needs a source.

    Returns:
        The reason, or None when the source is there, unchanged.
    """
    source = source_of(entry, reversal)
    if source is None:
        return _("the journal does not say where its content is")
    if source.is_file():
        changed = reversal is Reversal.MOVE_BACK and _changed(entry, source)
        return _("{path} changed since").format(path=source) if changed else None
    if reversal is Reversal.MOVE_BACK:
        return _("it is no longer at {path}: moved or renamed since").format(
            path=source
        )
    return _("its copy {path} is gone").format(path=source)


def source_of(entry: JournalEntry, reversal: Reversal) -> Path | None:
    """Return the file the content comes back from.

    Args:
        entry: The action.
        reversal: How it is undone.

    Returns:
        The kept copy, the quarantined copy, where a move put the file; None when
        there is none (an empty file, a folder) or the journal does not say.
    """
    source = {
        Reversal.COPY_FROM_KEEPER: entry.keeper,
        Reversal.UNQUARANTINE: entry.quarantine,
        Reversal.MOVE_BACK: entry.target,
    }.get(reversal)
    return Path(source) if source else None


def _changed(entry: JournalEntry, source: Path) -> bool:
    """Tell whether a moved file was modified since the move.

    Args:
        entry: The move.
        source: Where the file is now.

    Returns:
        True when its size, or its SHA-256 when journaled, differs.
    """
    if source.stat().st_size != entry.size:
        return True
    return entry.sha256 is not None and full_digest(source) != entry.sha256
