"""The turn each photo seems to need, guessed by `people` from its faces (0725).

One row per version of a photo (size, mtime) and pair of models: a photo changed since
(turned, edited, saved again) is guessed again by the next run. `turn` is 0 when no
turn is proposed (most photos), or the degrees clockwise (90, 180, 270). Keyed by path,
a table of `PATH_TABLES`: it follows a file `sort` or `undo` moves and leaves with a
file the audit finds gone.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.index.descriptions import PhotoVersion

CREATE_FACE_TURNS: Final = """
CREATE TABLE IF NOT EXISTS face_turns (
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    model TEXT NOT NULL,
    turn INTEGER NOT NULL,
    PRIMARY KEY (path, model)
)
"""
_GUESSED: Final = (
    "SELECT 1 FROM face_turns"
    " WHERE path = ? AND size = ? AND mtime_ns = ? AND model = ?"
)
_PUT: Final = (
    "INSERT OR REPLACE INTO face_turns (path, size, mtime_ns, model, turn)"
    " VALUES (?, ?, ?, ?, ?)"
)
# Only the current version of a file: a photo changed since is not proposed.
_PROPOSED: Final = (
    "SELECT face_turns.path, face_turns.turn FROM face_turns"
    " JOIN files ON files.path = face_turns.path AND files.size = face_turns.size"
    " AND files.mtime_ns = face_turns.mtime_ns"
    " WHERE face_turns.model = ? AND face_turns.turn != 0 ORDER BY face_turns.path"
)


@dataclass(frozen=True, slots=True)
class TurnGuess:
    """The turn guessed for one version of a photo: 0 for none."""

    path: Path
    size: int
    mtime_ns: int
    turn: int


class TurnStore:
    """Reads and writes the turns guessed with one pair of models."""

    def __init__(self, connection: sqlite3.Connection, model: str) -> None:
        """Bind the store to an open index and a pair of models.

        Args:
            connection: The index connection, tables prepared.
            model: `faces.models.FACE_MODEL`, or a test's.
        """
        self._connection = connection
        self._model = model

    def guessed(self, photo: PhotoVersion) -> bool:
        """Tell whether this version of a photo was guessed already.

        Args:
            photo: The photo, with its size and mtime.

        Returns:
            True when its guess (maybe no turn) is in the index.
        """
        key = (str(photo.path), photo.size, photo.mtime_ns, self._model)
        return self._connection.execute(_GUESSED, key).fetchone() is not None

    def put(self, guess: TurnGuess) -> None:
        """Keep the guess of a photo, and commit at once (Ctrl+C keeps it).

        Args:
            guess: The photo and its turn.
        """
        row = (str(guess.path), guess.size, guess.mtime_ns, self._model, guess.turn)
        self._connection.execute(_PUT, row)
        self._connection.commit()

    def proposed(self) -> tuple[tuple[Path, int], ...]:
        """The photos a turn is proposed for, current versions only.

        Returns:
            Each photo and its turn in degrees clockwise, by path.
        """
        return tuple(
            (Path(path), int(turn))
            for path, turn in self._connection.execute(_PROPOSED, (self._model,))
        )
