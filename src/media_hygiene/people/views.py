"""A section of the people page as the browser reads it: a strip, a sample, every face.

A section shows a few dozen faces spread over it, enough to tell who it is; the page
asks for every face before its photos can be set aside, so that each wrong face can
be taken out first. A verified section, already done, comes folded: a strip of a few
faces, enough to recognise the person; its sample is sent when it is opened (TODO
0323). The faces of photos set aside are left out and listed apart (TODO 0327).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.people.board import PeopleBoard
    from media_hygiene.people.sections import Section

SHOWN: Final = 60  # faces shown per section: enough to judge it
STRIP: Final = 8  # faces of a folded section: enough to recognise the person


@dataclass(frozen=True, slots=True)
class PageView:
    """How the page sees the photos: host paths, and those set aside."""

    host: Callable[[Path], str]  # container path → host path
    aside: frozenset[str] = frozenset()  # host paths of the files set aside


def spread(keys: tuple[int, ...], count: int) -> tuple[int, ...]:
    """At most `count` faces taken evenly over a section.

    Args:
        keys: The faces of the section, by number.
        count: How many at most.

    Returns:
        Them, in order.
    """
    step = max(1, len(keys) // count)
    return keys[::step][:count]


def section_view(
    board: PeopleBoard, section: Section, view: PageView
) -> dict[str, object]:
    """One section: its name, its kind, its counts, the faces shown and those hidden.

    Args:
        board: The faces of the page.
        section: The section.
        view: Host paths, and the files set aside.

    Returns:
        It, with a sample of faces spread over it; a strip only for a verified one
        (`folded`), whose sample `sample_view` sends on opening.
    """
    faces = section.faces
    hidden = {view.host(board.faces[key].path) for key in section.hidden}
    sample = spread(faces, STRIP if section.verified else SHOWN)
    return {
        "name": section.name,
        "verified": section.verified,
        "folded": section.verified,
        "faces": len(faces),
        "photos": len({view.host(board.faces[key].path) for key in faces}),
        "aside": len(hidden),
        "hidden": faces_view(board, section.hidden, view.host),
        "shown": faces_view(board, sample, view.host),
    }


def sample_view(
    board: PeopleBoard, section: Section, host: Callable[[Path], str]
) -> list[dict[str, object]]:
    """The sample of a section, as an opened section shows it.

    Args:
        board: The faces of the page.
        section: The section.
        host: Container path → host path.

    Returns:
        Up to `SHOWN` faces spread over it.
    """
    return faces_view(board, spread(section.faces, SHOWN), host)


def faces_view(
    board: PeopleBoard, keys: tuple[int, ...], host: Callable[[Path], str]
) -> list[dict[str, object]]:
    """Faces by number, each with the host path of its photo.

    Args:
        board: The faces of the page.
        keys: Their numbers.
        host: Container path → host path.

    Returns:
        One entry per face.
    """
    return [{"key": key, "photo": host(board.faces[key].path)} for key in keys]
