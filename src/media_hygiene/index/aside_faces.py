"""The faces of the people set aside, remembered without their photos (TODO 0328).

Setting aside every photo of someone on the people page keeps the vectors of the faces
sent, under one set-aside id (when, `YYYYMMDD-HHMMSS`) and the group's label. Not a row
of `PATH_TABLES`: no path at all, so the vectors outlive the photos, moved to the
quarantine by `clean`, then erased by `purge`. Taking the photos back (the page, or
`undo`, through `parked.unpark`) forgets their vectors; forgetting every face of the
index (`FaceStore.forget`) forgets these too. Version 17 of the index.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

CREATE_ASIDE_FACES: Final = """
CREATE TABLE IF NOT EXISTS aside_faces (
    aside TEXT NOT NULL,
    label TEXT NOT NULL,
    embedding BLOB NOT NULL,
    PRIMARY KEY (aside, embedding)
)
"""
FORGET_ALL: Final = "DELETE FROM aside_faces"
_PUT: Final = (
    "INSERT OR IGNORE INTO aside_faces (aside, label, embedding) VALUES (?, ?, ?)"
)
_FORGET: Final = "DELETE FROM aside_faces WHERE embedding = ?"
_EVERY: Final = "SELECT aside, label, embedding FROM aside_faces ORDER BY aside"


@dataclass(frozen=True, slots=True)
class AsideFaces:
    """The faces of one person set aside: when, under which label, their vectors."""

    aside: str  # `YYYYMMDD-HHMMSS`, the moment the first faces were set aside
    label: str
    embeddings: tuple[bytes, ...]


def remember(connection: sqlite3.Connection, faces: AsideFaces) -> None:
    """Keep the vectors of a person set aside, added to those of the same id.

    Args:
        connection: The index.
        faces: The person's faces.
    """
    connection.executemany(
        _PUT, [(faces.aside, faces.label, vector) for vector in faces.embeddings]
    )
    connection.commit()


def forget(connection: sqlite3.Connection, embeddings: Iterable[bytes]) -> None:
    """Forget these vectors, whoever they were remembered for; the caller commits.

    Args:
        connection: The index.
        embeddings: The vectors of the faces taken back.
    """
    connection.executemany(_FORGET, [(vector,) for vector in embeddings])


def remembered(connection: sqlite3.Connection) -> tuple[AsideFaces, ...]:
    """Every person set aside, oldest first.

    Args:
        connection: The index.

    Returns:
        Each one with its vectors; the label of the first row of each.
    """
    people: dict[str, tuple[str, list[bytes]]] = {}
    for aside, label, embedding in connection.execute(_EVERY):
        people.setdefault(str(aside), (str(label), []))[1].append(bytes(embedding))
    return tuple(
        AsideFaces(aside, label, tuple(vectors))
        for aside, (label, vectors) in people.items()
    )
