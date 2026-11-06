"""A named photo's content id: the index's, the file only without one (0635).

The audit has just given a digest to every healthy photo (0634): those are not read
again. A row counts only for the size and time the file has now: a photo edited, saved
over or touched since is read, whatever the index says. A photo with several faces is
read once a run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.hand_placed import Candidate, digest_of
from media_hygiene.config.photo_ref import content_id

if TYPE_CHECKING:
    import os
    import sqlite3
    from pathlib import Path

_ROW: Final = (
    "SELECT full_digest FROM files WHERE path = ? AND size = ? AND mtime_ns = ?"
)


@dataclass(slots=True)
class FaceIdReader:
    """Finds the ids of a run: the index first, each file read at most once.

    `connection` is the index, None when there is none: every file is then read.
    """

    connection: sqlite3.Connection | None = None
    _read: dict[Path, str | None] = field(default_factory=dict)

    def _indexed(self, path: Path, facts: os.stat_result) -> str | None:
        """The digest of a row that matches the file as it is now.

        Args:
            path: The photo.
            facts: Its stat.

        Returns:
            The digest; None without one.
        """
        if self.connection is None:
            return None
        row = self.connection.execute(
            _ROW, (str(path), facts.st_size, facts.st_mtime_ns)
        ).fetchone()
        return str(row[0]) if row and row[0] else None

    def needs_reading(self, path: Path) -> bool:
        """Whether `current_id` will read this file (the line the audit says).

        Args:
            path: The photo.

        Returns:
            True when it exists and the index has no digest for it as it is.
        """
        try:
            return self._indexed(path, path.stat()) is None
        except OSError:
            return False

    def current_id(self, path: Path) -> str | None:
        """The id of what a container path holds now.

        Args:
            path: The photo.

        Returns:
            Its id; None when it cannot be read.
        """
        if path in self._read:
            return self._read[path]
        try:
            facts = path.stat()
        except OSError:
            return None
        known = self._indexed(path, facts)
        sha = digest_of(Candidate(path, facts.st_size, known))
        found = None if sha is None else content_id(sha, facts.st_size)
        if known is None:
            self._read[path] = found
        return found
