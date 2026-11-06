"""*🏷 Tag…*: how many picked photos may be read while the page waits (0571).

A word is kept with an id of each photo's content. The index usually knows it; a file
it does not know is read whole, on the spot: 2 000 would hold the page for minutes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import ngettext

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.search.fts import SearchIndex

MOST_UNREAD: Final = 200  # a fixed cap, decided 2026-11-02: never a setting
_DIGEST: Final = "SELECT full_digest FROM files WHERE rowid = ?"


def too_many_unread(index: SearchIndex, keys: Iterable[int]) -> str:
    """Say why this many photos cannot be tagged now.

    Args:
        index: The open search.
        keys: The photos picked.

    Returns:
        The line to show; empty when at most `MOST_UNREAD` have to be read.
    """
    count = sum(1 for key in keys if _unread(index, key))
    if count <= MOST_UNREAD:
        return ""
    return ngettext(
        "{n} photo not analysed yet: run an audit first, or pick at most {most}",
        "{n} photos not analysed yet: run an audit first, or pick at most {most}",
        count,
    ).format(n=count, most=MOST_UNREAD)


def _unread(index: SearchIndex, key: int) -> bool:
    """Tell whether a known photo has no digest in the index.

    Args:
        index: The open search.
        key: A key of the search.

    Returns:
        True when it would be read whole; False for a key the search does not know.
    """
    if index.source_of(key) is None:
        return False
    row = index.connection.execute(_DIGEST, (key,)).fetchone()
    return not (row and row[0])
