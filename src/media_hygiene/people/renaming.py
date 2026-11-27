"""Rename a person, or merge two people when the new name is already someone's (0827).

Pure functions from `[people]` as written to the section to write. A rename keeps the
faces and the place in the list; the file follows the new name (`person_files` writes
it, the old one goes to `.history/`), but for a change of case only: Windows tells
`Manon.toml` from `manon.toml` apart from nothing, so the file stays. A new name that
is someone else's, whatever its case, is a merge: the person named keeps their name,
file and place; `faces` and `rejected` of both, each face once (the faces are keyed by
`<container path>#<n>` once loaded, whatever form the files wrote). A face confirmed by
one and ruled out by the other is a conflict: nothing is merged until the user said,
for each one, which list it goes to.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.config.people_files import FOLDER
from media_hygiene.people.person_files import SUFFIX, safe_name

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings, Person


@dataclass(frozen=True, slots=True)
class Renaming:
    """Who is renamed, the new name, and the conflicts' answers (None: not asked)."""

    name: str
    to: str
    named: frozenset[str] | None = None  # the faces in conflict kept as confirmed


@dataclass(frozen=True, slots=True)
class Renamed:
    """The section to write, or the conflicts waiting for the user."""

    section: PeopleSettings
    into: str = ""  # the person merged into; empty: a rename
    conflicts: tuple[str, ...] = ()  # nothing to write while not empty
    both: int = 0  # faces confirmed for both, kept once
    joined: int = 0  # faces the merged person brings

    @property
    def waiting(self) -> bool:
        """Tell whether the user must choose first.

        Returns:
            True while conflicts have no answer.
        """
        return bool(self.conflicts)


def rank_of(people: tuple[Person, ...], name: str) -> int | None:
    """The rank of a person, by name in any case.

    Args:
        people: The people.
        name: The name.

    Returns:
        The rank, or None.
    """
    wanted = name.strip().casefold()
    return next(
        (at for at, one in enumerate(people) if one.name.strip().casefold() == wanted),
        None,
    )


def rename(section: PeopleSettings, asked: Renaming) -> Renamed:
    """Rename a person, or merge them into the person already named so.

    Args:
        section: `[people]` as written.
        asked: Who, the new name, the conflicts' answers.

    Returns:
        The section to write, or the conflicts to show first.

    Raises:
        ValueError: Nobody has that name, or the new name is empty.
    """
    to = asked.to.strip()
    source = rank_of(section.person, asked.name)
    if source is None or not to:
        raise ValueError(asked.name if source is None else asked.to)
    people = list(section.person)
    target = rank_of(tuple(p for at, p in enumerate(people) if at != source), to)
    if target is None:
        people[source] = _renamed(people[source], to)
        return Renamed(section.model_copy(update={"person": tuple(people)}))
    target += target >= source  # its rank among every person
    return _merged(section, (people[source], people[target]), asked.named)


def _renamed(person: Person, to: str) -> Person:
    """The person under a new name; the file follows, unless the case only changed.

    Args:
        person: The person.
        to: The new name.

    Returns:
        The person.
    """
    same_file = f"{FOLDER}/{safe_name(to)}{SUFFIX}".casefold() == person.file.casefold()
    return person.model_copy(update={"name": to, "file": person.file * same_file})


def _merged(
    section: PeopleSettings,
    pair: tuple[Person, Person],
    named: frozenset[str] | None,
) -> Renamed:
    """Merge a person into another one.

    Args:
        section: `[people]` as written.
        pair: The person renamed, then the one already named so.
        named: The faces in conflict kept as confirmed; None: not asked yet.

    Returns:
        The section, or the conflicts.
    """
    source, target = pair
    conflicts = tuple(
        dict.fromkeys(
            (
                *(key for key in source.faces if key in set(target.rejected)),
                *(key for key in target.faces if key in set(source.rejected)),
            )
        )
    )
    if conflicts and named is None:
        return Renamed(section, target.name, conflicts)
    chosen = named or frozenset()
    faces = tuple(
        key
        for key in dict.fromkeys((*target.faces, *source.faces))
        if key not in conflicts or key in chosen
    )
    kept = set(faces)
    rejected = tuple(
        key
        for key in dict.fromkeys((*target.rejected, *source.rejected, *conflicts))
        if key not in kept
    )
    merged = target.model_copy(update={"faces": faces, "rejected": rejected})
    people = tuple(
        merged if one is target else one for one in section.person if one is not source
    )
    return Renamed(
        section.model_copy(update={"person": people}),
        target.name,
        both=len(set(source.faces) & set(target.faces)),
        joined=len(source.faces),
    )
