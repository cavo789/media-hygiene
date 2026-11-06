"""The group of each face: kept, a few new faces placed, or all regrouped (0588).

Grouping 20 000 faces takes seconds, at every opening of the page. Their groups are kept
in the index by a digest of each vector: no new face, nothing is computed. A few new
ones join the groups kept, which do not move. Once the faces that joined weigh more
than a tenth of the others, everything is grouped again: the groups cannot drift for
ever.
"""

from __future__ import annotations

import contextlib
import hashlib
import sqlite3
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.cluster import face_labels, join_labels
from media_hygiene.index.face_groups import add_labels, read_labels, replace_labels

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from numpy.typing import NDArray

    from media_hygiene.faces.cluster import Linkage

_MARK_BYTES: Final = 16
_REGROUP_SHARE: Final = 10  # all regrouped past one joined face per this many kept
_UNKNOWN: Final = -1


def kept_labels(
    connection: sqlite3.Connection,
    vectors: NDArray[np.float32],
    linkage: tuple[Linkage, str],
) -> NDArray[np.int64]:
    """Tell the group of each face, computing only what the index does not hold.

    Faces with the very same vector (copies of a photo) share one group.

    Args:
        connection: The open index; not written when it is read-only.
        vectors: One unit vector per face, one row each.
        linkage: How faces are linked, and the key of these settings (thresholds too).

    Returns:
        The group of each face.
    """
    links, key = linkage
    marks = [
        hashlib.blake2b(row.tobytes(), digest_size=_MARK_BYTES).digest()
        for row in vectors
    ]
    kept = read_labels(connection, key)
    labels = np.fromiter(
        (kept.labels.get(mark, _UNKNOWN) for mark in marks),
        dtype=np.int64,
        count=len(marks),
    )
    fresh = np.flatnonzero(labels == _UNKNOWN)
    known = len(marks) - len(fresh)
    if fresh.size == 0:
        return labels
    if (kept.joined + len(fresh)) * _REGROUP_SHARE > known:
        return _regrouped(connection, vectors, (links, key, marks))
    joined = join_labels(vectors, labels, links)
    by_mark = {marks[row]: int(joined[row]) for row in fresh.tolist()}
    _saved(add_labels, connection, (key, by_mark.items()))
    return np.fromiter(
        (by_mark.get(mark, kept.labels.get(mark, _UNKNOWN)) for mark in marks),
        dtype=np.int64,
        count=len(marks),
    )


def _regrouped(
    connection: sqlite3.Connection,
    vectors: NDArray[np.float32],
    how: tuple[Linkage, str, list[bytes]],
) -> NDArray[np.int64]:
    """Group every face and keep the result.

    Args:
        connection: The open index.
        vectors: The unit vectors.
        how: The linkage, the key of the settings, the digest of each face.

    Returns:
        The group of each face, the same at this opening as at the next.
    """
    links, key, marks = how
    labels = face_labels(vectors, links)
    by_mark = dict(zip(marks, labels.tolist(), strict=True))
    _saved(replace_labels, connection, (key, by_mark.items()))
    return np.fromiter((by_mark[mark] for mark in marks), np.int64, len(marks))


def _saved(
    write: Callable[[sqlite3.Connection, str, Iterable[tuple[bytes, int]]], None],
    connection: sqlite3.Connection,
    rows: tuple[str, Iterable[tuple[bytes, int]]],
) -> None:
    """Keep the groups if the index can be written; a cache not kept costs time only.

    Args:
        write: `replace_labels` or `add_labels`.
        connection: The open index.
        rows: The key and the rows.
    """
    with contextlib.suppress(sqlite3.OperationalError):
        write(connection, *rows)


def linkage_key(parts: Sequence[object]) -> str:
    """Name the settings a grouping depends on.

    Args:
        parts: The threshold, the neighbours, the faces left out.

    Returns:
        The key.
    """
    return repr(tuple(parts))
