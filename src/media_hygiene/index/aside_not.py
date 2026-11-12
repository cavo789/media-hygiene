"""The faces the user said are not a person set aside (TODO 0713).

The people page shows the faces that look like a person set aside; the cross on one, or
*Not them* on the block, keeps its vector here under that person's set-aside id, so the
face never comes back for that person, after a reload too. Another person set aside can
still show it. Like `aside_faces`, no path: only the vectors. Taking the person back
(every face of theirs forgotten) forgets these too; forgetting every face of the index
does as well. The table is created on first use, so an index of version 20 needs no
upgrade.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.index.aside_faces import FORGET_ALL

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

CREATE_ASIDE_NOT: Final = """
CREATE TABLE IF NOT EXISTS aside_not (
    aside TEXT NOT NULL,
    embedding BLOB NOT NULL,
    PRIMARY KEY (aside, embedding)
)
"""
# Forgetting every face: those set aside, then these (the table made first, for an
# index older than it).
FORGET_ASIDE: Final = (FORGET_ALL, CREATE_ASIDE_NOT, "DELETE FROM aside_not")
_PUT: Final = "INSERT OR IGNORE INTO aside_not (aside, embedding) VALUES (?, ?)"
_TAKE: Final = "DELETE FROM aside_not WHERE aside = ? AND embedding = ?"
_EVERY: Final = "SELECT aside, embedding FROM aside_not"
_ORPHANS: Final = (
    "DELETE FROM aside_not WHERE aside NOT IN (SELECT DISTINCT aside FROM aside_faces)"
)


def ignore(
    connection: sqlite3.Connection, aside: str, embeddings: Iterable[bytes]
) -> None:
    """Keep these faces as not the person set aside under `aside`.

    Args:
        connection: The index.
        aside: The person's set-aside id.
        embeddings: The vectors of the faces.
    """
    connection.execute(CREATE_ASIDE_NOT)
    connection.executemany(_PUT, [(aside, vector) for vector in embeddings])
    connection.commit()


def unignore(
    connection: sqlite3.Connection, aside: str, embeddings: Iterable[bytes]
) -> None:
    """Let these faces look like the person set aside under `aside` again.

    Args:
        connection: The index.
        aside: The person's set-aside id.
        embeddings: The vectors of the faces.
    """
    connection.execute(CREATE_ASIDE_NOT)
    connection.executemany(_TAKE, [(aside, vector) for vector in embeddings])
    connection.commit()


def ignored(connection: sqlite3.Connection) -> dict[str, frozenset[bytes]]:
    """The faces ignored, per person set aside.

    Args:
        connection: The index.

    Returns:
        Their vectors by set-aside id.
    """
    connection.execute(CREATE_ASIDE_NOT)
    found: dict[str, set[bytes]] = {}
    for aside, embedding in connection.execute(_EVERY):
        found.setdefault(str(aside), set()).add(bytes(embedding))
    return {aside: frozenset(vectors) for aside, vectors in found.items()}


def forget_orphans(connection: sqlite3.Connection) -> None:
    """Forget the ignores of the people no longer set aside; the caller commits.

    Args:
        connection: The index.
    """
    connection.execute(CREATE_ASIDE_NOT)
    connection.execute(_ORPHANS)
