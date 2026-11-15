"""The people a phone asks to keep off the TV, for one show only (0825).

A TV choice of the phone (at random, a folder, a month) may name people of
`[[people.person]]` to avoid: every photo where one of their faces shows is left out of
that show. Generous on purpose, a photo missed being the embarrassing case: the faces
named as theirs, and every face of the index within `LOOK_ALIKE` of their mean
(`person.likeness.close_rows`, the distance of `/person`). Nothing is stored: who is
avoided lives in the request, and the TV is told nothing. A name nobody bears is
ignored.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.people.folding import folded
from media_hygiene.people.known import Known
from media_hygiene.people.naming import id_of
from media_hygiene.person.likeness import close_rows
from media_hygiene.person.lookup import FaceIndex
from media_hygiene.review.serving import json_response

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from media_hygiene.review.http import Response
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class Avoided:
    """The photos left out of a show, and the names of the people they show."""

    paths: frozenset[Path] = frozenset()
    names: tuple[str, ...] = ()

    def kept(self, files: Iterable[Path]) -> tuple[list[Path], int]:
        """The files that may be shown, and how many were left out.

        Args:
            files: The files of the show, in its order.

        Returns:
            Those kept, in the same order, and the count of the others.
        """
        every = list(files)
        kept = [path for path in every if path not in self.paths]
        return kept, len(every) - len(kept)


def named_people(runtime: Runtime) -> list[str]:
    """The names a phone may avoid, alphabetical (case and accents aside).

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


def avoided(runtime: Runtime, asked: Sequence[str]) -> Avoided:
    """The photos of the people asked, generously (`paths_by_name`).

    Args:
        runtime: Settings, mount points and the host mapper.
        asked: The names the phone ticked; unknown ones are ignored.

    Returns:
        The photos to leave out and the names known among those asked.
    """
    found = paths_by_name(runtime, asked)
    paths: frozenset[Path] = frozenset().union(
        *(photos.sure | photos.guessed for photos in found.values())
    )
    return Avoided(paths, tuple(found))


def stated(response: Response, avoid: Avoided, left: int) -> Response:
    """The show's answer, saying how many photos were left out and for whom.

    Args:
        response: The answer of the show started.
        avoid: The people avoided.
        left: How many photos were left out.

    Returns:
        The answer with `left_out` and `avoided` added when people were avoided.
    """
    if not avoid.names or response.status != HTTPStatus.OK:
        return response
    body = json.loads(response.body)
    return json_response(
        response.status, {**body, "left_out": left, "avoided": list(avoid.names)}
    )
