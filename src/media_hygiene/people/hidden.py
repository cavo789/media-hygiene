"""The sections of the page without the faces of photos set aside (TODO 0327).

A photo set aside (`chosen` in the decisions file, from any page) waits for `clean
--decisions`: the user decided to remove it, so its faces are not shown, not counted,
not used to give a group to someone and never confirmed with the others. Each section
keeps them apart (`hidden`), so that the page can say how many are hidden there and
show them again, dimmed, to take one back. The groups themselves are not computed
again: taking a photo back shows it at once.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from media_hygiene.people.sections import Section, Sections, sections_of

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from media_hygiene.people.board import PeopleBoard
    from media_hygiene.people.naming import FaceName
    from media_hygiene.people.views import PageView


@dataclass(frozen=True, slots=True)
class Named:
    """The name of each face of the board, and the names each face is not."""

    names: tuple[FaceName, ...]
    ruled_out: Mapping[int, frozenset[str]] = field(default_factory=dict)


def page_sections(
    groups: Sequence[tuple[int, ...]], named: Named, hidden: frozenset[int]
) -> Sections:
    """The sections of the faces shown, each with its hidden faces.

    Args:
        groups: The groups of the board, largest first.
        named: The names of the faces.
        hidden: The faces whose photo is set aside.

    Returns:
        The sections of the visible faces; a section all of whose faces are hidden
        still shows, empty, so that they can be taken back.
    """
    every = sections_of(groups, named.names, named.ruled_out)
    if not hidden:
        return every
    visible = tuple(
        kept for group in groups if (kept := tuple(k for k in group if k not in hidden))
    )
    seen = sections_of(visible, named.names, named.ruled_out)
    shown = list(seen.shown)
    for section in every.shown:
        apart = tuple(key for key in section.faces if key in hidden)
        if not apart:
            continue
        at = _place(shown, section)
        if at is None:
            shown.append(Section((), section.name, section.verified, apart))
        else:
            shown[at] = replace(shown[at], hidden=(*shown[at].hidden, *apart))
    return Sections(tuple(shown), seen.ignored)


def _place(shown: list[Section], section: Section) -> int | None:
    """The section shown that stands for one computed with every face.

    Args:
        shown: The sections of the visible faces.
        section: A section of every face.

    Returns:
        The rank of the one sharing a visible face, else the same person's of the
        same kind; None when there is none.
    """
    faces = set(section.faces)
    for rank, one in enumerate(shown):
        if one.name == section.name and faces.intersection(one.faces):
            return rank
    for rank, one in enumerate(shown):
        if section.name and (one.name, one.verified) == (
            section.name,
            section.verified,
        ):
            return rank
    return None


def not_aside(
    board: PeopleBoard, keys: tuple[int, ...], view: PageView
) -> tuple[int, ...]:
    """The faces whose photo is not set aside: a name never confirms a hidden face.

    Args:
        board: The faces of the page.
        keys: Face numbers sent by the page.
        view: Host paths, and the files set aside.

    Returns:
        Those numbers, the faces of photos set aside (and unknown numbers) left out.
    """
    return tuple(
        key
        for key in keys
        if (face := board.face(str(key))) is not None
        and view.host(face.path) not in view.aside
    )
