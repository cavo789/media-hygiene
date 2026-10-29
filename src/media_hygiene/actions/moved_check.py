"""Whether a file `undo` brings content back from changed since the action."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry


def changed_since(entry: JournalEntry, source: Path) -> bool:
    """Tell whether a file was modified since the action: a move, a link removed.

    Args:
        entry: The action.
        source: Where the file is now.

    Returns:
        True when its size, or its SHA-256 when journaled, differs.
    """
    if source.stat().st_size != entry.size:
        return True
    return entry.sha256 is not None and full_digest(source) != entry.sha256
