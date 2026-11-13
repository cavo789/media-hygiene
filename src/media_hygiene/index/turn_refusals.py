"""The turns refused on the *Photos to straighten* page, kept by path (0802).

Keyed by path, a table of `PATH_TABLES`: a refusal follows its photo when `sort` or
`undo` moves it, or when the audit finds it renamed in Explorer (`index.rematch`), and
leaves with a photo the audit finds gone. Any version of the photo: refused once, never
proposed again.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

CREATE_TURN_REFUSALS: Final = """
CREATE TABLE IF NOT EXISTS turn_refusals (
    path TEXT PRIMARY KEY
)
"""
_REFUSE: Final = "INSERT OR IGNORE INTO turn_refusals (path) VALUES (?)"
_TAKE_BACK: Final = "DELETE FROM turn_refusals WHERE path = ?"
_EVERY: Final = "SELECT path FROM turn_refusals"


class TurnRefusals:
    """Reads and writes the photos whose proposed turn was refused."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Bind to an open index, its tables prepared.

        Args:
            connection: The index connection.
        """
        self._connection = connection

    def refuse(self, paths: Iterable[Path]) -> None:
        """Keep these photos' turns refused, committed at once.

        Args:
            paths: The photos.
        """
        self._connection.executemany(_REFUSE, ((str(path),) for path in paths))
        self._connection.commit()

    def take_back(self, paths: Iterable[Path]) -> None:
        """Propose these photos' turns again, committed at once.

        Args:
            paths: The photos.
        """
        self._connection.executemany(_TAKE_BACK, ((str(path),) for path in paths))
        self._connection.commit()

    def refused(self) -> frozenset[Path]:
        """The photos whose turn was refused.

        Returns:
            Their paths.
        """
        return frozenset(Path(path) for (path,) in self._connection.execute(_EVERY))
