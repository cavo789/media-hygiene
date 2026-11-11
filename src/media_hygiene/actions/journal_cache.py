"""A journal read once while it does not change: the home page asks each run 3 times.

`status` (the home page's state) summarises every run, asks whether it can still be
undone and looks for the newest push: three full reads of every journal, each line
validated, at each opening of the page. The entries are kept by the journal's
identity (inode, size, modification time): an append, an atomic rewrite (new inode)
or a `touch` reads it again.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import read_journal

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry

# Journals kept decoded: a few hundred runs fit, a few MB each at most.
_KEPT: Final = 256


def read_journal_once(file: Path) -> list[JournalEntry]:
    """Read every entry of a journal, decoded once per version of the file.

    Args:
        file: Journal path.

    Returns:
        The entries, in write order (a new list: the caller may change it).

    Raises:
        JournalError: The journal is missing or a line is corrupt.
    """
    try:
        stat = file.stat()
    except OSError:
        return read_journal(file)  # says why, as before
    return list(_decoded(file, (stat.st_ino, stat.st_size, stat.st_mtime_ns)))


@lru_cache(maxsize=_KEPT)
def _decoded(file: Path, identity: tuple[int, int, int]) -> tuple[JournalEntry, ...]:
    """Decode a journal once per identity.

    Args:
        file: Journal path.
        identity: Its inode, size and modification time (the cache key).

    Returns:
        The entries (frozen models).
    """
    del identity  # the key only
    return tuple(read_journal(file))
