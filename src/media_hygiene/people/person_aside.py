"""`POST /api/person-aside`: set aside a person's photos, and drop the name (0836).

Seeing first: `check` lists the person's photos (faces confirmed or given by the tool,
photos already set aside left out), one per photo: those where they are the only face
found, ticked by default, and those where others are too, listed and never touched
(the default decided for 0836: an ex is set aside, not the family photos they are on).
The page sends back the photos still ticked; only those are set aside, by the people
page's desk (`aside.AsideDesk`: the decisions file, *Apply now*, `clean --decisions`
journals the move, `undo` brings them back). With `drop`, the name goes too: its file
and its link leave `config.toml` (both kept in `/config/.history/` first); the person
dropped is kept by this desk until the page stops, so the Undo of the page puts the
name back (`restore`), read back from the disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.i18n import _
from media_hygiene.people.aside import AsideAsked
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.renaming import rank_of

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings, Person
    from media_hygiene.people.aside import AsideDesk
    from media_hygiene.people.board import PeopleBoard
    from media_hygiene.people.sections import Sections
    from media_hygiene.people.views import PageView

PERSON_ASIDE_PATH: Final = "/api/person-aside"
_NAME_LENGTH: Final = 100
_MAX_PHOTOS: Final = 100_000


class PersonAsideAsked(BaseModel):
    """What the page asks: list the photos, set the ticked ones aside, or restore."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=_NAME_LENGTH)
    check: bool = False
    keys: tuple[int, ...] = Field(default=(), max_length=_MAX_PHOTOS)  # face numbers
    drop: bool = False  # the name goes too
    restore: bool = False  # the name dropped comes back


@dataclass(frozen=True, slots=True)
class PersonPhotos:
    """The board, its sections now, and how a photo is shown."""

    board: PeopleBoard
    sections: Sections
    view: PageView


@dataclass(slots=True)
class PersonAside:
    """Sets aside a person's photos and drops the name; remembers it to put it back."""

    desk: AsideDesk
    config_file: Path | None
    adopt: Callable[[PeopleSettings], None]
    dropped: dict[str, Person] = field(default_factory=dict)

    def answer(
        self, asked: PersonAsideAsked, photos: PersonPhotos
    ) -> dict[str, object]:
        """List, set aside, or restore, then say what the files hold.

        Args:
            asked: What the page asks.
            photos: The faces of the page.

        Returns:
            The photos (`alone`, `others`), or the decisions file and the names.

        Raises:
            ValueError: Nothing to set aside, no name to drop or restore.
            OSError: A file cannot be written.
        """
        alone, others = _photos(asked.name, photos)
        if asked.check:
            return {"alone": alone, "others": others}
        if asked.restore:
            return {"saved": self._restore(asked.name)}
        offered = {int(str(photo["face"])) for photo in alone}
        keys = tuple(key for key in asked.keys if key in offered)
        if not keys:
            raise ValueError(_("no photo of {name} is ticked").format(name=asked.name))
        add = AsideAsked(action="add", faces=keys, label=asked.name, remember=False)
        said = self.desk.change(photos.board, add)
        if asked.drop:
            said = {**said, "saved": self._drop(asked.name)}
        return {**said, "set": list(keys)}

    def _drop(self, name: str) -> str:
        """Drop the name from `config.toml`, kept here to put it back.

        Args:
            name: The person.

        Returns:
            What the file holds now.

        Raises:
            ValueError: No `config.toml`, nobody of that name.
        """
        section, at = self._section(name)
        if at is None:
            raise ValueError(_("nobody is named {name}").format(name=name))
        person = section.person[at]
        people = tuple(one for one in section.person if one is not person)
        self._save(section.model_copy(update={"person": people}))
        self.dropped[person.name.casefold()] = person
        return self._said(person.name)

    def _restore(self, name: str) -> str:
        """Put a dropped name back, its faces and its file.

        Args:
            name: The person.

        Returns:
            What the file holds now.

        Raises:
            ValueError: That name was not dropped by this page.
        """
        person = self.dropped.pop(name.casefold(), None)
        if person is None:
            raise ValueError(_("nobody is named {name}").format(name=name))
        section, at = self._section(name)
        if at is None:
            people = (*section.person, person.model_copy(update={"file": ""}))
            self._save(section.model_copy(update={"person": people}))
        return self._said(person.name)

    def _section(self, name: str) -> tuple[PeopleSettings, int | None]:
        if self.config_file is None:
            raise ValueError(
                _("names are kept in config.toml: mount a folder of yours on /config")
            )
        section = read_people(self.config_file)
        return section, rank_of(section.person, name)

    def _save(self, section: PeopleSettings) -> None:
        if self.config_file is None:
            return
        save_people(self.config_file, section)
        self.adopt(read_people(self.config_file))

    def _said(self, name: str) -> str:
        _section, at = self._section(name)
        if at is None:
            return _("Saved in config.toml, read back: nobody is named {name}.").format(
                name=name
            )
        return _("Saved in config.toml, read back: {name} is named again.").format(
            name=name
        )


def _photos(
    name: str, photos: PersonPhotos
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """The person's photos, one face each: alone on it, or with others.

    Args:
        name: The person.
        photos: The faces of the page.

    Returns:
        The photos where they are the only face found, then the others.
    """
    wanted = name.strip().casefold()
    board, seen = photos.board, set()
    alone: list[dict[str, object]] = []
    others: list[dict[str, object]] = []
    for section in photos.sections.shown:
        if section.name.strip().casefold() != wanted:
            continue
        for key in section.faces:
            path = board.faces[key].path
            if path in seen:
                continue
            seen.add(path)
            row = {"face": key, "where": photos.view.host(path)}
            (alone if board.crowd[path] == 1 else others).append(row)
    return alone, others
