"""Which group each face fell in: opening `people` does not group them again (0588).

Not a row of `PATH_TABLES`: a face is known by a digest of its vector, no path at all.
A photo moved or renamed (by `sort`, by `undo`, by hand) keeps its group; a photo edited
gets a new vector when it is analysed again, so a new face to place. `key` says which
settings the groups were made with: other settings find no row, and regroup. Forgetting
every face of the index (`FaceStore.forget`) forgets these too. Version 18 of the index.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

CREATE_FACE_GROUPS: Final = """
CREATE TABLE IF NOT EXISTS face_groups (
    key TEXT NOT NULL,
    mark BLOB NOT NULL,
    label INTEGER NOT NULL,
    joined INTEGER NOT NULL,
    PRIMARY KEY (key, mark)
)
"""
FORGET_GROUPS: Final = "DELETE FROM face_groups"
_READ: Final = "SELECT mark, label, joined FROM face_groups WHERE key = ?"
_PUT: Final = (
    "INSERT OR REPLACE INTO face_groups (key, mark, label, joined) VALUES (?, ?, ?, ?)"
)


@dataclass(frozen=True, slots=True)
class KeptLabels:
    """The groups kept: the group of each digest, and how many faces joined later."""

    labels: dict[bytes, int]
    joined: int


def read_labels(connection: sqlite3.Connection, key: str) -> KeptLabels:
    """Read the groups made with these settings.

    Args:
        connection: The open index.
        key: The settings.

    Returns:
        The groups; empty when none were kept.
    """
    labels: dict[bytes, int] = {}
    joined = 0
    for mark, label, late in connection.execute(_READ, (key,)):
        labels[bytes(mark)] = int(label)
        joined += int(late)
    return KeptLabels(labels, joined)


def replace_labels(
    connection: sqlite3.Connection, key: str, labels: Iterable[tuple[bytes, int]]
) -> None:
    """Keep the groups of a full grouping, instead of any earlier ones.

    Args:
        connection: The open index.
        key: The settings.
        labels: Each digest and its group.
    """
    connection.execute(FORGET_GROUPS)
    connection.executemany(_PUT, ((key, *row, 0) for row in labels))
    connection.commit()


def add_labels(
    connection: sqlite3.Connection, key: str, labels: Iterable[tuple[bytes, int]]
) -> None:
    """Keep the groups of faces that joined the others.

    Args:
        connection: The open index.
        key: The settings.
        labels: Each new digest and its group.
    """
    connection.executemany(_PUT, ((key, *row, 1) for row in labels))
    connection.commit()
