"""The photos of the people named, for the slideshow's "Avoid some people" (0825).

Generous on purpose, a photo missed being the embarrassing case: the faces named as
theirs (✓), and every face of the index within `LOOK_ALIKE` of their mean (≈,
`person.likeness.close_rows`, the distance of `/person`). The remote offers the people
seen on its show (`slideshow_people`) and sets their photos out; the names ticked are
remembered in `[slideshow] avoid` (0834). A name nobody bears is ignored.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.people.folding import folded
from media_hygiene.people.known import Known
from media_hygiene.people.naming import id_of
from media_hygiene.person.likeness import close_rows
from media_hygiene.person.lookup import FaceIndex

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


def named_people(runtime: Runtime) -> list[str]:
    """The names that may be avoided, alphabetical (case and accents aside).

    Args:
        runtime: Settings, mount points and the host mapper.

    Returns:
        Each name once; none when nobody is named.
    """
    names = dict.fromkeys(person.name for person in runtime.settings.people.person)
    return sorted(names, key=folded)


@dataclass(frozen=True, slots=True)
class PersonPhotos:
    """A person's photos: those with a face named as theirs (✓), those guessed (≈)."""

    sure: frozenset[Path] = frozenset()
    guessed: frozenset[Path] = frozenset()  # a face close to their mean, none named


def paths_by_name(runtime: Runtime, asked: Sequence[str]) -> dict[str, PersonPhotos]:
    """The photos of each person asked, generously.

    The faces named as theirs, and every face of the index within `LOOK_ALIKE` of
    their mean (`close_rows`); the face index is read once for all of them.

    Args:
        runtime: Settings, mount points and the host mapper.
        asked: The names asked; unknown ones are ignored.

    Returns:
        By name known (as `[[people.person]]` writes it), their photos.
    """
    wanted = {folded(name) for name in asked}
    names = [name for name in named_people(runtime) if folded(name) in wanted]
    if not names:
        return {}
    faces = FaceIndex(runtime.index_file)
    every = faces.every
    if not every:
        return dict.fromkeys(names, PersonPhotos())
    known = Known.of(every, runtime.settings.people)
    by_id = {id_of(face): face.path for face in every}
    found: dict[str, PersonPhotos] = {}
    for name in names:
        rows = [row for row, owner in enumerate(known.names) if owner == name]
        if not rows:
            found[name] = PersonPhotos()
            continue
        close, _ = close_rows(known.vectors[rows], faces.vectors)
        sure = frozenset(by_id[known.ids[row]] for row in rows)
        near = frozenset(every[row].path for row in close.tolist()) - sure
        found[name] = PersonPhotos(sure, near)
    return found
