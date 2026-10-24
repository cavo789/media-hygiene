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
from media_hygiene.people.hidden import Named, page_sections
from media_hygiene.people.known import Known
from media_hygiene.people.naming import id_of, name_all
from media_hygiene.people.proof import followed_line, proof_line
from media_hygiene.people.views import section_view

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.people.board import PeopleBoard
    from media_hygiene.people.sections import Section, Sections
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
        self._named = self._name()

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
        sections = self.sections(view)
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
        self._named = self._name()
        return proof_line(back, change) + followed_line(original, written)

    def _name(self) -> Named:
        """Name every face, and note who each one was taken out of.

        The ids of moved photos are followed (TODO 0146).

        Returns:
            The name of each face, and the names each face is not, by number.
        """
        known = Known.of(self._every, self._settings, self._moves)
        ruled_out = {
            key: names
            for key, face in enumerate(self.board.faces)
            if (names := known.rejected.get(id_of(face)))
        }
        return Named(name_all(self.board.faces, known), ruled_out)

    def sections(self, view: PageView) -> Sections:
        """The sections, the faces of the photos set aside apart (TODO 0327).

        Args:
            view: Host paths, and the files set aside.

        Returns:
            The sections the page shows.
        """
        hidden = frozenset(
            key
            for key, face in enumerate(self.board.faces)
            if view.aside and view.host(face.path) in view.aside
        )
        return page_sections(self.board.groups, self._named, hidden)

    def section(self, key: str, view: PageView) -> Section | None:
        """The section shown that holds a face.

        Args:
            key: The number of one of its faces, from the page.
            view: Host paths, and the files set aside.

        Returns:
            It; None for a number no section shows.
        """
        if not key.isdigit():
            return None
        shown = self.sections(view).shown
        return next((one for one in shown if int(key) in one.faces), None)
