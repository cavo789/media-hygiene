"""Where the copies `clean` removed lay, kept by the path of the file kept (0207).

A folder someone named (`Mariage Julie 2015`) or a file name someone chose would go
with the copy `clean` removes: each copy deleted or set aside with a kept file leaves
a row here. Keyed by the kept file's path, a row of `PATH_TABLES`: it follows the kept
file when `sort`, `undo` or the user moves it (`moves`, `rematch`), is parked with it
when a later clean sets it aside, and is forgotten when it is proven gone. `undo` of
the clean removes the rows of the copies it brings back. Version 14 of the index.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.former import FormerCopy

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

CREATE_FORMER_NAMES: Final = """
CREATE TABLE IF NOT EXISTS former_names (
    path TEXT NOT NULL,
    former TEXT NOT NULL,
    root TEXT NOT NULL,
    run TEXT NOT NULL,
    PRIMARY KEY (path, former)
)
"""
_SAVE: Final = (
    "INSERT OR REPLACE INTO former_names (path, former, root, run) VALUES (?, ?, ?, ?)"
)
_BACK: Final = "DELETE FROM former_names WHERE former = ? AND run = ?"
_EVERY: Final = "SELECT path, former, root FROM former_names ORDER BY path, former"
_OF: Final = "SELECT former, root FROM former_names WHERE path = ? ORDER BY former"


def remember_former(
    connection: sqlite3.Connection,
    run: str,
    removed: Sequence[tuple[str, FormerCopy]],
) -> None:
    """Keep where each removed copy lay, by the path of its kept file.

    Args:
        connection: The index.
        run: The clean that removed them.
        removed: The kept file's path and the copy removed, for each copy.
    """
    connection.executemany(
        _SAVE,
        [(kept, str(copy.path), str(copy.root), run) for kept, copy in removed],
    )


def forget_former(
    connection: sqlite3.Connection, run: str, restored: Iterable[str]
) -> None:
    """Drop the rows of copies `undo` brought back: they have their own name again.

    Args:
        connection: The index.
        run: The clean undone.
        restored: The paths of the copies restored (container paths).
    """
    connection.executemany(_BACK, [(path, run) for path in restored])


def former_copies(connection: sqlite3.Connection) -> dict[Path, tuple[FormerCopy, ...]]:
    """Every removed copy remembered, by the path of the file kept.

    Args:
        connection: The index.

    Returns:
        The copies of each kept file; none with an index read-only and older than
        version 14.
    """
    found: dict[Path, list[FormerCopy]] = defaultdict(list)
    try:
        rows = connection.execute(_EVERY).fetchall()
    except sqlite3.OperationalError:  # an index read-only, older than the table
        return {}
    for path, former, root in rows:
        found[Path(path)].append(FormerCopy(Path(former), Path(root)))
    return {path: tuple(copies) for path, copies in found.items()}


def former_of(connection: sqlite3.Connection, path: Path) -> tuple[FormerCopy, ...]:
    """The removed copies of one kept file.

    Args:
        connection: The index.
        path: The kept file.

    Returns:
        Its removed copies, in path order.
    """
    rows = connection.execute(_OF, (str(path),)).fetchall()
    return tuple(FormerCopy(Path(former), Path(root)) for former, root in rows)
