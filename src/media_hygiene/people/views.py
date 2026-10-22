"""A section of the people page as the browser reads it: a sample, or every face.

A section shows a few dozen faces spread over it, enough to tell who it is; the page
asks for every face before its photos can be set aside, so that each wrong face can
be taken out first. Each section says how many of its photos are set aside already.
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


@dataclass(frozen=True, slots=True)
class PageView:
    """How the page sees the photos: host paths, and those set aside."""

    host: Callable[[Path], str]  # container path → host path
    aside: frozenset[str] = frozenset()  # host paths of the files set aside


def section_view(
    board: PeopleBoard, section: Section, view: PageView
) -> dict[str, object]:
    """One section: its name, verified or attributed, its counts, the faces shown.

    Args:
        board: The faces of the page.
        section: The section.
        view: Host paths, and the files set aside.

    Returns:
        It, with a sample of faces spread over it.
    """
    faces = section.faces
    step = max(1, len(faces) // SHOWN)
    photos = {view.host(board.faces[key].path) for key in faces}
    return {
        "name": section.name,
        "verified": section.verified,
        "faces": len(faces),
        "photos": len(photos),
        "aside": len(photos & view.aside),
        "shown": faces_view(board, faces[::step][:SHOWN], view.host),
    }


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
