"""Recognise the files moved or renamed outside media-hygiene, before forgetting them.

A folder renamed in Explorer makes its old paths gone and its new paths unknown: the
work the cache holds (checks, fingerprints, faces, the vision model's descriptions)
would be done again. A gone file and a new one with the same size and modification
time (Explorer keeps it when it moves or copies) are the same file when their partial
digests (first and last 64 KiB) agree too: its rows follow it (TODO 0147). Never on
size and time alone.
"""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import Sizes
from media_hygiene.scan.hashing import partial_digest

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence

    from media_hygiene.scan.models import MediaFile

_GONE_ROW: Final = "SELECT size, mtime_ns, partial_digest FROM files WHERE path = ?"

type _Key = tuple[int, int, str]


def rematched(
    connection: sqlite3.Connection, gone: Sequence[str], newcomers: Sequence[MediaFile]
) -> list[tuple[str, str]]:
    """Pair the files gone with the new files that are them, moved or renamed.

    Args:
        connection: The index.
        gone: The paths the walk proves gone.
        newcomers: The files listed that the index does not know.

    Returns:
        Old and new path of each file recognised.
    """
    waiting: defaultdict[_Key, list[str]] = defaultdict(list)
    for path in gone:
        row = connection.execute(_GONE_ROW, (path,)).fetchone()
        if row is not None and row[2]:
            waiting[(row[0], row[1], row[2])].append(path)
    sizes = {(size, mtime) for size, mtime, _digest in waiting}
    candidates = [file for file in newcomers if (file.size, file.mtime_ns) in sizes]
    if not candidates:
        return []
    with ThreadPoolExecutor(Sizes.IO_CONCURRENCY) as pool:
        digests = list(pool.map(_digest_or_none, candidates))
    pairs: list[tuple[str, str]] = []
    for file, digest in zip(candidates, digests, strict=True):
        olds = waiting.get((file.size, file.mtime_ns, digest or ""))
        if olds:
            pairs.append((_take(olds, file.path.name), str(file.path)))
    return pairs


def _take(olds: list[str], name: str) -> str:
    """Take the gone path to pair: the one of the same name first (identical copies).

    Args:
        olds: The gone paths of the same size, time and partial digest.
        name: The name of the new file.

    Returns:
        The gone path taken out of `olds`.
    """
    same = next(
        (index for index, old in enumerate(olds) if old.endswith(f"/{name}")), -1
    )
    return olds.pop(same)


def _digest_or_none(file: MediaFile) -> str | None:
    """The partial digest of a new file (runs in a worker thread).

    Args:
        file: The file.

    Returns:
        Its digest, None when it cannot be read.
    """
    try:
        return partial_digest(file.path)
    except OSError:
        return None
