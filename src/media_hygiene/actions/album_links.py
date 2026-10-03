"""Hard links of an album: why one cannot be made, and when one may be removed.

A hard link is a second name for the same bytes: removing one name never removes the
bytes while another name is left. `undo` removes an album's name only when it can see
that other name: the original the journal recorded still exists, at another path, and is
the very same file (same disk, same inode). The link count (`st_nlink`) is not trusted:
Docker Desktop's Windows mounts may report it wrongly. When the original was moved or
renamed since, the album's name is kept and the reason told: an album never loses the
last copy of a photo.
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
        The translated reason, or None when the original is provably another name of
        the same file, so removing the album's name leaves the photo whole.
    """
    link = Path(entry.path)
    if not link.is_file():
        return _("it is no longer in the album: removed already")
    original = Path(entry.keeper) if entry.keeper else None
    if original is None or original.resolve() == link.resolve():
        return _("the journal does not say which photo it is a name of: kept")
    if not original.is_file():
        return _(
            "its original {path} is no longer there (moved or renamed since?): "
            "kept, it may be the last name of the photo"
        ).format(path=original)
    if not link.samefile(original):
        return _("it is no longer a name of {path}: kept").format(path=original)
    return None
