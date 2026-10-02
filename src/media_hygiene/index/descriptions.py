"""What a local model saw in a photo, and the categories it chose: cached in the index.

A description is kept for one version of the file, one model and one prompt: a run
describes only what is missing, and Ctrl+C keeps what is done (each answer is
committed at once). Mappings are keyed by a digest of everything they depend on, so
that going back to an earlier list of categories costs nothing.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.ai.models import Description

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

_SELECT: Final = (
    "SELECT size, mtime_ns, description, tags, seconds FROM descriptions"
    " WHERE path = ? AND model = ? AND prompt = ?"
)
_UPSERT: Final = (
    "INSERT OR REPLACE INTO descriptions"
    " (path, size, mtime_ns, model, prompt, description, tags, seconds)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)
_SECONDS: Final = "SELECT seconds FROM descriptions WHERE model = ? AND seconds > 0"
_MAPPING: Final = "SELECT category FROM subject_mappings WHERE key = ?"
_PUT_MAPPING: Final = (
    "INSERT OR REPLACE INTO subject_mappings (key, category) VALUES (?, ?)"
)


@dataclass(frozen=True, slots=True)
class PhotoVersion:
    """One version of a photo: a description of another version is stale."""

    path: Path
    size: int
    mtime_ns: int


class DescriptionStore:
    """The descriptions of one model and one prompt, and the mappings of all."""

    def __init__(self, connection: sqlite3.Connection, asked: tuple[str, str]) -> None:
        """Bind the store to a model and a prompt version.

        Args:
            connection: The index connection, tables prepared.
            asked: The vision model, and the version of the describe prompt.
        """
        self._connection = connection
        self._model, self._prompt = asked

    def get(self, photo: PhotoVersion) -> Description | None:
        """The description of this version of a photo.

        Args:
            photo: The photo.

        Returns:
            It, or None when never described (or the file changed since).
        """
        row = self._connection.execute(
            _SELECT, (str(photo.path), self._model, self._prompt)
        ).fetchone()
        if row is None or (row[0], row[1]) != (photo.size, photo.mtime_ns):
            return None
        tags = json.loads(row[3])
        return Description(row[2], tuple(str(tag) for tag in tags), float(row[4]))

    def put(self, photo: PhotoVersion, description: Description) -> None:
        """Remember a description at once: an interrupted run keeps it.

        Args:
            photo: The photo.
            description: What the model saw.
        """
        self._connection.execute(
            _UPSERT,
            (
                str(photo.path),
                photo.size,
                photo.mtime_ns,
                self._model,
                self._prompt,
                description.text,
                json.dumps(list(description.tags)),
                description.seconds,
            ),
        )
        self._connection.commit()

    def seconds_per_photo(self) -> float | None:
        """How long this model takes to describe a photo, on this machine.

        Returns:
            The median of the times recorded, or None before the first one.
        """
        rows = self._connection.execute(_SECONDS, (self._model,)).fetchall()
        return statistics.median(row[0] for row in rows) if rows else None

    def mapping(self, key: str) -> str | None:
        """A category chosen before.

        Args:
            key: The digest of the description, model, prompt and categories.

        Returns:
            The category (empty: none fits), or None when never asked.
        """
        row = self._connection.execute(_MAPPING, (key,)).fetchone()
        return str(row[0]) if row is not None else None

    def put_mapping(self, key: str, category: str) -> None:
        """Remember a category chosen.

        Args:
            key: The digest of what it depends on.
            category: The category (empty: none fits).
        """
        self._connection.execute(_PUT_MAPPING, (key, category))
        self._connection.commit()
