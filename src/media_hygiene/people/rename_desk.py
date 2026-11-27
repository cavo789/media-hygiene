"""`POST …/api/rename`: rename a person, or merge two people (0827).

`check` asks what would happen, said before it runs: a rename, or a merge ("Ana (12
faces) joins Anna (340 faces): 3 faces in both are kept once") with the faces in
conflict (confirmed by one, ruled out by the other), each shown with its photo when the
page has it. The page sends back the faces of the conflicts the user keeps as
confirmed (the keys the check gave, any other ignored); without that answer a merge
with conflicts writes nothing. The save goes through `save_people` (the files first,
`config.toml` atomic, the file of the person merged removed: both in `.history/`), then
the settings naming the person follow (`name_follow`); everything said is read back.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.i18n import _, ngettext
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.name_follow import follow_name
from media_hygiene.people.renaming import Renamed, Renaming, rank_of, rename

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.config.people_settings import PeopleSettings

_NAME_LENGTH: Final = 100
_SEPARATOR: Final = "#"


class RenameAsked(BaseModel):
    """What the page asks: check, or save, a new name for a person."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=_NAME_LENGTH)
    to: str = Field(min_length=1, max_length=_NAME_LENGTH)
    check: bool = False
    named: tuple[str, ...] | None = None  # conflicts kept as confirmed; None: unasked


@dataclass(frozen=True, slots=True)
class FaceShown:
    """How the page shows a face: its number there (None: none), its host path."""

    number: Callable[[str], int | None]
    host: Callable[[Path], str]


@dataclass(frozen=True, slots=True)
class RenameDesk:
    """Renames in `config.toml`, then hands the settings read back to the page."""

    config_file: Path | None
    shown: FaceShown
    adopt: Callable[[PeopleSettings], None]  # the page names its faces again

    def answer(self, asked: RenameAsked) -> dict[str, object]:
        """Say what a rename would do, or do it and read it back.

        Args:
            asked: The person, the new name, the answers.

        Returns:
            `check` (the sentence, the conflicts), or `saved` and `people`.

        Raises:
            ValueError: No `config.toml`, nobody of that name.
            OSError: A file cannot be written.
        """
        if self.config_file is None:
            raise ValueError(
                _("names are kept in config.toml: mount a folder of yours on /config")
            )
        section = read_people(self.config_file)
        named = None if asked.named is None else frozenset(asked.named)
        try:
            done = rename(section, Renaming(asked.name, asked.to, named))
        except ValueError:
            raise ValueError(
                _("nobody is named {name}").format(name=asked.name)
            ) from None
        if asked.check or done.waiting:
            return {"check": self._check(section, asked, done)}
        save_people(self.config_file, done.section)
        followed = follow_name(self.config_file, asked.name, done.into or asked.to)
        back = read_people(self.config_file)
        self.adopt(back)
        return {
            "saved": _saved(back, done.into or asked.to.strip(), followed),
            "people": [person.name for person in back.person],
        }

    def _check(
        self, section: PeopleSettings, asked: RenameAsked, done: Renamed
    ) -> dict[str, object]:
        """What the rename will do, said before it runs.

        Args:
            section: `[people]` as written.
            asked: The person and the new name.
            done: The rename, computed.

        Returns:
            The sentence, the person merged into, the conflicts.
        """
        old = section.person[rank_of(section.person, asked.name) or 0]
        conflicts = [
            {
                "key": key,
                "photo": self.shown.number(key),
                "where": self.shown.host(Path(key.rsplit(_SEPARATOR, 1)[0])),
                "named_by": old.name if key in old.faces else done.into,
            }
            for key in done.conflicts
        ]
        if not done.into:
            sentence = _("{old} becomes {new}; every face is kept.")
            return {"sentence": sentence.format(old=old.name, new=asked.to.strip())}
        into = section.person[rank_of(section.person, done.into) or 0]
        sentence = _("{old} ({n} faces) joins {into} ({m} faces).").format(
            old=old.name, n=len(old.faces), into=into.name, m=len(into.faces)
        )
        both = len(set(old.faces) & set(into.faces))
        sentence += " " + ngettext(
            "{n} face in both is kept once.", "{n} faces in both are kept once.", both
        ).format(n=both)
        return {"sentence": sentence, "into": into.name, "conflicts": conflicts}


def _saved(back: PeopleSettings, name: str, followed: tuple[str, ...]) -> str:
    """The line the page shows: what the files hold now.

    Args:
        back: `[people]` read back from the disk.
        name: The person's name now.
        followed: The other settings rewritten.

    Returns:
        One line, and what did not follow.
    """
    at = rank_of(back.person, name)
    if at is None:
        return _("Saved in config.toml, read back: nobody is named {name}.").format(
            name=name
        )
    person = back.person[at]
    line = ngettext(
        "Saved in config.toml, read back: {name}, {count} confirmed face.",
        "Saved in config.toml, read back: {name}, {count} confirmed faces.",
        len(person.faces),
    ).format(name=person.name, count=len(person.faces))
    if followed:
        line += " " + _("Renamed there too: {where}.").format(where=", ".join(followed))
    return (
        line
        + " "
        + _(
            "Albums keep their names, and XMP sidecars the names they hold"
            " until 'xmp' runs again."
        )
    )
