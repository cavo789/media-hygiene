"""A face left unnamed by a cross on a wrong name, and the cross undone (2026-11-16).

One meaning for every cross on a name, `/person`, the large views and the library's
tiles: "not this one, and I do not want to name it". The name is ruled out and the
face is marked `unguessed` (`people/unguessed.toml`): no other name is guessed for
it. Undone (*Put back*), the mark goes with the rejection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.people.changes import Naming, put_back, reject_faces

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings


def left_unnamed(section: PeopleSettings, naming: Naming) -> PeopleSettings:
    """Rule the name out of the faces, and guess no other name for them.

    Args:
        section: `[people]` as written.
        naming: The name ruled out, and the faces.

    Returns:
        The section to write.
    """
    ruled = reject_faces(section, naming)
    marks = tuple(dict.fromkeys((*ruled.unguessed, *naming.faces)))
    return ruled.model_copy(update={"unguessed": marks})


def named_again(
    section: PeopleSettings, naming: Naming, confirmed: tuple[str, ...]
) -> PeopleSettings:
    """Undo `left_unnamed`: the rejection and the mark go, those confirmed return.

    Args:
        section: `[people]` as written.
        naming: The name, and the faces the cross left unnamed.
        confirmed: Those of them the user had confirmed: back in `faces`.

    Returns:
        The section to write.
    """
    back = put_back(section, naming, confirmed)
    taken = frozenset(naming.faces)
    marks = tuple(key for key in back.unguessed if key not in taken)
    return back.model_copy(update={"unguessed": marks})
