"""What the people page shows and changes: the sections, and the names saved.

Every change is written into `config.toml`, then read back from the disk: the page
shows what the next run will read, and says so (proof, not promise). Without a
writable `/config`, the page shows the names already given and saves none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.people.changes import Naming, give_name, ignore_faces, reject_faces
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_ids
from media_hygiene.people.naming import Known, id_of, name_all
from media_hygiene.people.proof import followed_line, proof_line
from media_hygiene.people.sections import sections_of
from media_hygiene.people.views import faces_view, section_view

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.people.board import PeopleBoard
    from media_hygiene.people.views import PageView


@dataclass(frozen=True, slots=True)
class NamesFile:
    """Where the names are saved (None: not mounted), the settings, the moves."""

    config_file: Path | None
    settings: PeopleSettings
    moves: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Change:
    """What the page asks: `name`, `ignore` or `reject` faces, by board number."""

    action: str
    naming: Naming


class Roster:
    """The board, the faces of reference, and the names as last read from disk."""

    def __init__(
        self, board: PeopleBoard, every: tuple[StoredFace, ...], names: NamesFile
    ) -> None:
        """Name the faces of the board.

        Args:
            board: The faces and groups of the page.
            every: Every face of the index, to find the confirmed ones.
            names: Where the names are saved, and the settings.
        """
        self.board = board
        self._every = every
        self._file = names.config_file
        self._settings = names.settings
        self._moves = names.moves
        self._names = name_all(board.faces, self._known())

    @property
    def writable(self) -> bool:
        """Tell whether names can be saved.

        Returns:
            True with a `config.toml` to write.
        """
        return self._file is not None

    def state(self, view: PageView) -> dict[str, object]:
        """The sections as the page reads them.

        Args:
            view: Host paths, and the files set aside.

        Returns:
            The sections, the names known, the counts.
        """
        sections = sections_of(self.board.groups, self._names)
        board = self.board
        return {
            "alone": self.board.alone,
            "ignored": sections.ignored,
            "writable": self.writable,
            "people": [person.name for person in self._settings.person],
            "sections": [
                section_view(board, section, view) for section in sections.shown
            ],
        }

    def change(self, change: Change) -> str:
        """Write a change into `config.toml`, read it back, name the faces again.

        Args:
            change: What the page asks, faces as ids.

        Returns:
            What the file holds now, said in one line.

        Raises:
            ValueError: No `config.toml` to write, or the file is invalid.
            OSError: The file cannot be written.
        """
        if self._file is None:
            raise ValueError(
                _("names are kept in config.toml: mount a folder of yours on /config")
            )
        present = {str(face.path) for face in self._every}
        original = read_people(self._file)
        written = follow_ids(original, self._moves, present)
        if change.action == "ignore":
            wanted = ignore_faces(written, change.naming.faces)
        elif change.action == "reject":
            wanted = reject_faces(written, change.naming)
        else:
            wanted = give_name(written, change.naming)
        save_people(self._file, wanted)
        back = read_people(self._file)
        self._settings = self._settings.model_copy(
            update={"person": back.person, "ignored": back.ignored}
        )
        self._names = name_all(self.board.faces, self._known())
        return proof_line(back, change) + followed_line(original, written)

    def _known(self) -> Known:
        """The faces of reference, ids of moved photos followed (TODO 0146).

        Returns:
            The references.
        """
        return Known.of(self._every, self._settings, self._moves)

    def whole(self, key: str, host: Callable[[Path], str]) -> list[dict[str, object]]:
        """Every face of the section a face is in, to check each one.

        Args:
            key: The number of one of its faces, from the page.
            host: Container path → host path.

        Returns:
            Its faces; none for a number no section holds.
        """
        if not key.isdigit():
            return []
        sections = sections_of(self.board.groups, self._names).shown
        found = next((one for one in sections if int(key) in one.faces), None)
        return [] if found is None else faces_view(self.board, found.faces, host)

    def ids(self, keys: tuple[int, ...]) -> tuple[str, ...]:
        """The ids of faces of the board.

        Args:
            keys: Their numbers.

        Returns:
            Their ids; unknown numbers are left out.
        """
        return tuple(
            id_of(face)
            for key in keys
            if (face := self.board.face(str(key))) is not None
        )
