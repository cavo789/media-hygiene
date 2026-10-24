"""The faces the search page can correct: every face, the references, who is where.

Made once, at the first cross or *Why this name?* of a page (TODO 0317, 0318), from the
index (`/cache`) and `[people]`; then kept up to date by each change the page saves:
the names of the photo changed, and the references read back from `config.toml`.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.faces.models import FACE_MODEL
from media_hygiene.i18n import _
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.moves import load_moves
from media_hygiene.people.known import Known
from media_hygiene.people.naming import id_of, name_all
from media_hygiene.search.people_words import faces_named

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace


@dataclass(slots=True)
class Seen:
    """Every face of the index, the references, and the faces named on each photo."""

    faces: tuple[StoredFace, ...]
    known: Known
    moves: dict[str, str]
    # Each photo, each name on it, the ids of its faces there: changed by the page.
    named: dict[Path, dict[str, tuple[str, ...]]] = field(default_factory=dict)
    numbers: dict[str, int] = field(default_factory=dict)  # face id → its rank

    @classmethod
    def load(cls, connection: sqlite3.Connection, settings: PeopleSettings) -> Seen:
        """Read the faces and name them, as the search did at its start.

        Args:
            connection: The index, read-only.
            settings: `[people]`, with the names.

        Returns:
            Them; none with an index older than faces.
        """
        try:
            faces = FaceStore(connection, FACE_MODEL).faces()
        except sqlite3.OperationalError:  # no `faces` table: `people` never ran
            faces = ()
        moves = load_moves(connection) if faces else {}
        known = Known.of(faces, settings, moves)
        named = faces_named(faces, name_all(faces, known)) if settings.person else {}
        numbers = {id_of(face): rank for rank, face in enumerate(faces)}
        return cls(faces, known, moves, named, numbers)

    def present(self) -> set[str]:
        """The paths of the photos that have faces, to follow moved ids.

        Returns:
            Them.
        """
        return {str(face.path) for face in self.faces}

    def renamed(self, settings: PeopleSettings) -> None:
        """Take the references again from `[people]` as read back.

        Args:
            settings: `[people]`, read back from the disk.
        """
        self.known = Known.of(self.faces, settings, self.moves)

    def face(self, number: int) -> StoredFace | None:
        """A face by its rank.

        Args:
            number: Its rank, from the page.

        Returns:
            It, or None for any other number.
        """
        return self.faces[number] if 0 <= number < len(self.faces) else None

    def ids(self, path: Path, name: str, number: int | None) -> tuple[str, ...]:
        """The faces of a photo a change is about: every one of the name, or one.

        Args:
            path: The photo.
            name: The name on it.
            number: One face (its rank), or None for every face of the name.

        Returns:
            Their ids.

        Raises:
            ValueError: The name is not on the photo, or the face is not that name's.
        """
        ids = self.named.get(path, {}).get(name, ())
        if number is not None:
            face = self.face(number)
            ids = tuple(key for key in ids if face is not None and key == id_of(face))
        if not ids:
            message = _("nobody named {name} on this photo").format(name=name)
            raise ValueError(message)
        return ids
