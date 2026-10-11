"""What the people page shows and changes: the sections, and the names saved.

Every change is written into `config.toml`, then read back from the disk: the page
shows what the next run will read, and says so (proof, not promise). Without a
writable `/config`, the page shows the names already given and saves none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _, ngettext
from media_hygiene.people.changes import Naming, give_name, ignore_faces, reject_faces
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.naming import Known, id_of, name_all
from media_hygiene.people.sections import sections_of

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.people.board import PeopleBoard
    from media_hygiene.people.sections import Section

SHOWN: Final = 60  # faces shown per section: enough to judge it


@dataclass(frozen=True, slots=True)
class NamesFile:
    """Where the names are saved (None: not mounted), and the settings of the run."""

    config_file: Path | None
    settings: PeopleSettings


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
        self._names = name_all(board.faces, Known.of(every, self._settings))

    @property
    def writable(self) -> bool:
        """Tell whether names can be saved.

        Returns:
            True with a `config.toml` to write.
        """
        return self._file is not None

    def state(self, host: Callable[[Path], str]) -> dict[str, object]:
        """The sections as the page reads them.

        Args:
            host: Container path → host path.

        Returns:
            The sections, the names known, the counts.
        """
        sections = sections_of(self.board.groups, self._names)
        return {
            "alone": self.board.alone,
            "ignored": sections.ignored,
            "writable": self.writable,
            "people": [person.name for person in self._settings.person],
            "sections": [self._section(section, host) for section in sections.shown],
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
        written = read_people(self._file)
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
        self._names = name_all(self.board.faces, Known.of(self._every, self._settings))
        return _proof(back, change)

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

    def _section(
        self, section: Section, host: Callable[[Path], str]
    ) -> dict[str, object]:
        """One section as the page reads it.

        Args:
            section: The section.
            host: Container path → host path.

        Returns:
            Its name or suggestion, its counts, the faces shown, spread over it.
        """
        faces = section.faces
        step = max(1, len(faces) // SHOWN)
        shown = faces[::step][:SHOWN]
        return {
            "name": section.name,
            "suggested": section.suggested,
            "faces": len(faces),
            "photos": len({self.board.faces[key].path for key in faces}),
            "shown": [
                {"key": key, "photo": host(self.board.faces[key].path)} for key in shown
            ],
        }


def _proof(back: PeopleSettings, change: Change) -> str:
    """Say what `config.toml` holds now for the change.

    Args:
        back: `[people]` read back from the disk.
        change: The change.

    Returns:
        One line.
    """
    if change.action == "ignore":
        count = len(back.ignored)
        return ngettext(
            "Saved in config.toml, read back: {count} face ignored.",
            "Saved in config.toml, read back: {count} faces ignored.",
            count,
        ).format(count=count)
    folded = change.naming.name.strip().casefold()
    person = next((p for p in back.person if p.name.casefold() == folded), None)
    if person is None:
        return _("Saved in config.toml, read back: nobody is named {name}.").format(
            name=change.naming.name
        )
    return ngettext(
        "Saved in config.toml, read back: {name}, {count} confirmed face.",
        "Saved in config.toml, read back: {name}, {count} confirmed faces.",
        len(person.faces),
    ).format(name=person.name, count=len(person.faces))
