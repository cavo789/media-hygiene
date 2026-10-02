"""Hard links of an album: why one cannot be made, and when one may be removed.

A hard link is a second name for the same bytes: removing one name never removes the
bytes while another name is left. `undo` relies on that, and on nothing else: it removes
an album's name only when the file still has another one (the original, wherever a
`sort` moved it since), so an album never loses the last copy of a photo.
"""

from __future__ import annotations

import errno
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry

# Errors that every other link of the run would meet too: the run stops at the first.
UNSUPPORTED: Final = frozenset(
    {errno.EXDEV, errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS}
)
_LAST_NAME: Final = 1


def why_not(exc: OSError) -> str:
    """Explain, in the user's words, why a hard link could not be made.

    Args:
        exc: What `os.link` raised.

    Returns:
        The translated reason.
    """
    if exc.errno == errno.EXDEV:
        return _(
            "the album and this file are on two disks or two mounts: a hard link "
            "cannot cross them"
        )
    if exc.errno in UNSUPPORTED:
        return _("this disk does not support hard links (FAT, exFAT, a network share?)")
    if exc.errno == errno.EEXIST:
        return _("a file of that name is in the album already")
    if exc.errno == errno.EMLINK:
        return _("this file has too many names already")
    return exc.strerror or str(exc)


def link_blocker(entry: JournalEntry) -> str | None:
    """Tell why the link an album run made cannot be removed right now.

    Args:
        entry: The `link` action: the name made in the album (`path`), and the file
            it is a name of (`keeper`).

    Returns:
        The translated reason, or None when removing it leaves the file whole.
    """
    link = Path(entry.path)
    if not link.is_file():
        return _("it is no longer in the album: removed already")
    if link.stat().st_nlink <= _LAST_NAME:
        return _("it is the last name left of this file: kept")
    return None
