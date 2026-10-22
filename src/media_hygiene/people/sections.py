"""The sections of the page: the people by name first, then suggestions, then the rest.

A group holding faces the user confirmed is that person's; the groups of one person
are shown together. A group whose faces mostly come close to someone, none confirmed,
is a suggestion ("Chloé?"). A group mostly ignored is not shown again. A face the
user took out of someone (`rejected`) leaves their section: it stays in its group, but
is never shown again under that name.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.people.naming import How

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from media_hygiene.people.naming import FaceName

_HALF: Final = 2


@dataclass(frozen=True, slots=True)
class Section:
    """Faces shown together: one person's groups, or one group."""

    faces: tuple[int, ...]  # numbers of the board
    name: str = ""  # the person, confirmed
    suggested: str = ""  # the person they look like, none confirmed


@dataclass(frozen=True, slots=True)
class Sections:
    """What the page shows, and how many groups the user ignored."""

    shown: tuple[Section, ...]
    ignored: int


def sections_of(
    groups: Sequence[tuple[int, ...]],
    names: Sequence[FaceName],
    ruled_out: Mapping[int, frozenset[str]] | None = None,
) -> Sections:
    """Sort the groups into sections.

    Args:
        groups: The groups, as face numbers, largest first.
        names: The name of each face, by number.
        ruled_out: The names each face is not, by number (the user took it out).

    Returns:
        The named people (most faces first), the suggestions, then the others.
    """
    ruled_out = ruled_out or {}
    people: dict[str, list[int]] = {}
    suggested: list[Section] = []
    unnamed: list[Section] = []
    ignored = 0
    for group in groups:
        hows = Counter(names[key].how for key in group)
        if hows[How.IGNORED] * _HALF > len(group):
            ignored += 1
            continue
        confirmed = Counter(
            names[key].name for key in group if names[key].how is How.CONFIRMED
        )
        if confirmed:
            name = confirmed.most_common(1)[0][0]
            people.setdefault(name, []).extend(_without(group, name, ruled_out))
            continue
        assigned = Counter(
            names[key].name for key in group if names[key].how is How.ASSIGNED
        )
        best = assigned.most_common(1)
        if best and best[0][1] * _HALF >= len(group):
            name = best[0][0]
            kept = _without(group, name, ruled_out)
            if kept:
                suggested.append(Section(kept, suggested=name))
        else:
            unnamed.append(Section(group))
    named = sorted(
        (Section(tuple(faces), name=name) for name, faces in people.items() if faces),
        key=lambda section: -len(section.faces),
    )
    return Sections((*named, *suggested, *unnamed), ignored)


def _without(
    group: tuple[int, ...], name: str, ruled_out: Mapping[int, frozenset[str]]
) -> tuple[int, ...]:
    """A group without the faces the user took out of someone.

    Args:
        group: The face numbers.
        name: The person the group is shown as.
        ruled_out: The names each face is not, by number.

    Returns:
        The faces left, in order.
    """
    return tuple(key for key in group if name not in ruled_out.get(key, ()))
