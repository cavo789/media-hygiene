"""Undo the copies of an `import` run: remove each one while it holds what was copied.

The journal keeps each copy's SHA-256 once it was proven (`done`): a copy edited since
in another application, or never proven (the run stopped), is kept and the reason told.
The backup it came from is never touched.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import Status
from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry


def copy_blocker(entry: JournalEntry) -> str | None:
    """Tell why a copy cannot be removed.

    Args:
        entry: The copy's latest journal state.

    Returns:
        The translated reason, or None when it holds what was copied.
    """
    path = Path(entry.path)
    if not path.is_file():
        return _("the copy is gone already")
    if entry.sha256 is None:
        return _("the copy was never proven (the run stopped): kept")
    if full_digest(path) != entry.sha256:
        return _("the copy changed since (edited in another application?): kept")
    return None


def never_copied(entry: JournalEntry) -> bool:
    """Tell whether a run stopped before this copy got its name.

    Args:
        entry: The copy, maybe `pending`.

    Returns:
        True for a `pending` copy whose file is not there: nothing to undo.
    """
    return entry.status is Status.PENDING and not Path(entry.path).exists()
