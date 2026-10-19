"""Undo a copy made a link (0213): its name becomes an independent file again.

The bytes are copied from the name itself to a draft in its folder, proven identical,
given back the copy's date, then `os.replace` puts the draft over the link: the name
always holds the photo. The kept file is not needed to read the bytes, but it tells
whether the name is still a link: an independent file is left alone. Without the kept
file (moved or deleted since), the name may still have another name somewhere: it is
made independent all the same, which costs room and loses nothing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import Status
from media_hygiene.actions.link_move import same_file
from media_hygiene.actions.no_overwrite import copy_exclusive
from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry

_DRAFT_SUFFIX: Final = ".media-hygiene-copy"


def separate_blocker(entry: JournalEntry) -> str | None:
    """Tell why a name made a link cannot become an independent file now.

    Args:
        entry: The `link-duplicate` action: the copy's name (`path`), the kept file.

    Returns:
        The translated reason, or None when the name is still a link to the kept file,
        or the kept file is no longer there to tell.
    """
    path = Path(entry.path)
    if not path.is_file():
        return _("it is no longer there")
    if not entry.keeper:
        return _("the journal does not say which photo it is a name of: kept")
    keeper = Path(entry.keeper)
    if keeper.is_file() and not same_file(path, keeper):
        return _("it is an independent file already")
    return (
        None  # its kept file moved or deleted since: the copy costs room, loses nothing
    )


def never_linked(entry: JournalEntry) -> bool:
    """Tell whether a run stopped before this copy became a link.

    Args:
        entry: The `link-duplicate` action.

    Returns:
        True for a `pending` action whose name is not a link to the kept file.
    """
    if entry.status is not Status.PENDING or not entry.keeper:
        return False
    return not same_file(Path(entry.path), Path(entry.keeper))


def separate(entry: JournalEntry) -> None:
    """Make the name an independent file again, holding the same bytes.

    Args:
        entry: The `link-duplicate` action `separate_blocker` allowed.

    Raises:
        OSError: The copy could not be made or is not identical (the name stays a
            link, the draft is removed).
        BaseException: Interrupted (Ctrl+C): raised again once the draft is removed.
    """
    path = Path(entry.path)
    draft = path.with_name(f".{path.name}{_DRAFT_SUFFIX}")
    read = copy_exclusive(path, draft)
    try:
        _proven(draft, read)
        os.utime(draft, ns=(entry.mtime_ns, entry.mtime_ns))  # the copy's own date
        draft.replace(path)
    except BaseException:
        draft.unlink(missing_ok=True)
        raise


def _proven(draft: Path, read: str) -> None:
    """Check that a copy holds what was read from its source.

    Args:
        draft: The copy, just written.
        read: The SHA-256 of what was read from the source.

    Raises:
        OSError: The copy differs.
    """
    if full_digest(draft) != read:
        raise OSError(_("the restored copy does not match the original"))
