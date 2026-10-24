"""What the page changes in `[people]`: name faces, ignore them, take them from someone.

Pure functions from the section as written to the section to write. A face belongs to
one person at most: naming it takes it from anyone else and from the ignored ones. A
second group named like an existing person adds to their faces (a child at every
age); a person left without any face is dropped.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.config.people_settings import Person

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.config.people_settings import PeopleSettings

_NAME_LENGTH: Final = 100


class NamesAsked(BaseModel):
    """`POST /api/people`: what to do with which faces, by board number."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["name", "ignore", "reject"]
    name: str = Field(default="", max_length=_NAME_LENGTH)
    faces: tuple[int, ...] = Field(min_length=1)
    removed: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class Naming:
    """Faces to give a name, and those the user took out of the group first."""

    name: str
    faces: tuple[str, ...]
    removed: tuple[str, ...] = ()


def give_name(section: PeopleSettings, naming: Naming) -> PeopleSettings:
    """Give faces a name, adding them to that person or creating them.

    Args:
        section: `[people]` as written.
        naming: The name, the faces, those taken out.

    Returns:
        The section to write.
    """
    name = naming.name.strip()
    taken = frozenset(naming.faces)
    people = [_without(person, taken) for person in section.person]
    found = _find(people, name)
    person = people[found] if found is not None else Person(name=name)
    person = person.model_copy(
        update={
            "faces": _added(person.faces, naming.faces),
            "rejected": _added(
                tuple(key for key in person.rejected if key not in taken),
                naming.removed,
            ),
        }
    )
    if found is None:
        people.append(person)
    else:
        people[found] = person
    ignored = tuple(key for key in section.ignored if key not in taken)
    return _kept(section, people, ignored)


def ignore_faces(section: PeopleSettings, faces: tuple[str, ...]) -> PeopleSettings:
    """Ignore faces: strangers, posters, statues.

    Args:
        section: `[people]` as written.
        faces: The faces.

    Returns:
        The section to write.
    """
    taken = frozenset(faces)
    people = [_without(person, taken) for person in section.person]
    return _kept(section, people, _added(section.ignored, faces))


def reject_faces(section: PeopleSettings, naming: Naming) -> PeopleSettings:
    """Say that faces are not someone's: never named so again.

    Args:
        section: `[people]` as written.
        naming: The name, and the faces that are not theirs.

    Returns:
        The section to write; unchanged for an unknown name.
    """
    people = list(section.person)
    found = _find(people, naming.name.strip())
    if found is None:
        return section
    taken = frozenset(naming.faces)
    person = _without(people[found], taken)
    people[found] = person.model_copy(
        update={"rejected": _added(person.rejected, naming.faces)}
    )
    return _kept(section, people, section.ignored)


def put_back(
    section: PeopleSettings, naming: Naming, confirmed: tuple[str, ...]
) -> PeopleSettings:
    """Undo `reject_faces`: the faces leave `rejected`, those confirmed before return.

    Args:
        section: `[people]` as written.
        naming: The name, and the faces rejected.
        confirmed: Those of them the user had confirmed: back in `faces`.

    Returns:
        The section to write.
    """
    if confirmed:
        section = give_name(section, Naming(naming.name, confirmed))
    people = list(section.person)
    found = _find(people, naming.name.strip())
    if found is None:
        return section
    taken = frozenset(naming.faces)
    rejected = tuple(key for key in people[found].rejected if key not in taken)
    people[found] = people[found].model_copy(update={"rejected": rejected})
    return _kept(section, people, section.ignored)


def _find(people: list[Person], name: str) -> int | None:
    """The rank of a person, by name in any case.

    Args:
        people: The people.
        name: The name.

    Returns:
        The rank, or None.
    """
    folded = name.casefold()
    for rank, person in enumerate(people):
        if person.name.strip().casefold() == folded:
            return rank
    return None


def _without(person: Person, taken: frozenset[str]) -> Person:
    """A person without some faces.

    Args:
        person: The person.
        taken: The faces to take away.

    Returns:
        The person.
    """
    kept = tuple(key for key in person.faces if key not in taken)
    return person.model_copy(update={"faces": kept})


def _added(known: tuple[str, ...], more: Iterable[str]) -> tuple[str, ...]:
    """Ids added at the end, each once.

    Args:
        known: The ids already there.
        more: Those to add.

    Returns:
        Every id once, in order.
    """
    return tuple(dict.fromkeys((*known, *more)))


def _kept(
    section: PeopleSettings, people: list[Person], ignored: tuple[str, ...]
) -> PeopleSettings:
    """The section with its new people (those with faces) and ignored faces.

    Args:
        section: `[people]` as written.
        people: The people.
        ignored: The ignored faces.

    Returns:
        The section.
    """
    alive = tuple(person for person in people if person.faces)
    return section.model_copy(update={"person": alive, "ignored": ignored})
