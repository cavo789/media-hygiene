"""The sections of the page: each person verified then attributed, then the rest.

A person shows in two sections at most: the faces the user confirmed (*verified*), and
the faces the tool gives them (*attributed*): the rest of the groups holding faces they
confirmed, and the groups whose faces mostly come close to them, none confirmed. The
attributed faces are checked a page at a time; once confirmed they move to the verified
section, and an empty section is not shown. A group mostly ignored is not shown again. A
face the user took out of someone (`rejected`) is never shown under that name again.
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
_SETTLED: Final = frozenset({How.CONFIRMED, How.IGNORED})  # never attributed again


@dataclass(frozen=True, slots=True)
class Section:
    """Faces shown together: one person's verified or attributed faces, or one group."""

    faces: tuple[int, ...]  # numbers of the board
    name: str = ""  # the person; empty for a group nobody is given
    verified: bool = False  # True: faces the user confirmed
    hidden: tuple[int, ...] = ()  # its faces on photos set aside: not shown (0327)


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
        The people (those with verified faces first, most faces first), each verified
        then attributed, then the groups nobody is given.
    """
    ruled_out = ruled_out or {}
    verified: dict[str, list[int]] = {}
    for key in (key for group in groups for key in group):
        if names[key].how is How.CONFIRMED:
            verified.setdefault(names[key].name, []).append(key)
    attributed: dict[str, list[int]] = {}
    unnamed: list[Section] = []
    ignored = 0
    for group in groups:
        hows = Counter(names[key].how for key in group)
        if hows[How.IGNORED] * _HALF > len(group):
            ignored += 1
            continue
        owner = _owner(group, names)
        if not owner:
            unnamed.append(Section(group))
            continue
        attributed.setdefault(owner, []).extend(
            key
            for key in group
            if names[key].how not in _SETTLED and owner not in ruled_out.get(key, ())
        )
    people = sorted(
        {*verified, *attributed},
        key=lambda name: (
            name not in verified,
            -len(verified.get(name, ())) - len(attributed.get(name, ())),
        ),
    )
    shown = [
        section
        for name in people
        for section in (
            Section(tuple(verified.get(name, ())), name, verified=True),
            Section(tuple(attributed.get(name, ())), name),
        )
        if section.faces
    ]
    return Sections((*shown, *unnamed), ignored)


def _owner(group: tuple[int, ...], names: Sequence[FaceName]) -> str:
    """The person a group is given to: most of its confirmed faces, else of its faces.

    Args:
        group: The face numbers.
        names: The name of each face, by number.

    Returns:
        The name; empty when nobody holds the group.
    """
    confirmed = Counter(
        names[key].name for key in group if names[key].how is How.CONFIRMED
    )
    if confirmed:
        return confirmed.most_common(1)[0][0]
    assigned = Counter(
        names[key].name for key in group if names[key].how is How.ASSIGNED
    )
    best = assigned.most_common(1)
    return best[0][0] if best and best[0][1] * _HALF >= len(group) else ""
