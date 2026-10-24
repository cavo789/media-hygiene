"""The `person` words of the search: who is on each photo, made from the faces.

Made at each search (and each `classify` run with a `person` rule) from the faces of
the index (`/cache`) and the names of `config.toml` (`[[people.person]]`): a face
confirmed on the people page, or close enough to one, gives its photo the person's
name. Suggestions never do. Nothing is written: the words live in memory only.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from media_hygiene.faces.models import FACE_MODEL
from media_hygiene.i18n import _
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.moves import load_moves
from media_hygiene.people.folding import folded
from media_hygiene.people.known import Known
from media_hygiene.people.naming import id_of, name_all
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.people.naming import FaceName
    from media_hygiene.search.query import SearchQuery


def people_words(
    connection: sqlite3.Connection, settings: PeopleSettings
) -> dict[Path, tuple[str, ...]]:
    """The names of the people on each photo of the index.

    Args:
        connection: The index, read-only.
        settings: `[people]`, with the names.

    Returns:
        Each photo with someone named on it, and their names in the file's order;
        nothing without names, or with an index older than faces.
    """
    return words_of(people_faces(connection, settings), settings)


def people_faces(
    connection: sqlite3.Connection, settings: PeopleSettings
) -> dict[Path, dict[str, tuple[str, ...]]]:
    """Which faces give each photo each name: `<path>#<n>` ids (TODO 0317).

    Args:
        connection: The index, read-only.
        settings: `[people]`, with the names.

    Returns:
        Each photo with someone named on it, each name with the ids of its faces
        there (a photo may have two faces given the same person).
    """
    if not settings.person:
        return {}
    try:
        faces = FaceStore(connection, FACE_MODEL).faces()
    except sqlite3.OperationalError:  # no `faces` table: `people` never ran
        return {}
    known = Known.of(faces, settings, load_moves(connection))
    return faces_named(faces, name_all(faces, known))


def faces_named(
    faces: Sequence[StoredFace], names: Sequence[FaceName]
) -> dict[Path, dict[str, tuple[str, ...]]]:
    """Gather the faces named by photo, then by name.

    Args:
        faces: The faces.
        names: The name of each.

    Returns:
        Each photo with someone named on it, each name with the ids of its faces.
    """
    found: dict[Path, dict[str, tuple[str, ...]]] = {}
    for face, name in zip(faces, names, strict=True):
        if name.named:
            named = found.setdefault(face.path, {})
            named[name.name] = (*named.get(name.name, ()), id_of(face))
    return found


def words_of(
    faces: Mapping[Path, Mapping[str, tuple[str, ...]]], settings: PeopleSettings
) -> dict[Path, tuple[str, ...]]:
    """The names on each photo, in the order of the file.

    Args:
        faces: The faces of each name on each photo.
        settings: `[people]`, with the names in order.

    Returns:
        Each photo with at least one name, and its names.
    """
    order = {person.name: rank for rank, person in enumerate(settings.person)}
    return {
        path: tuple(sorted(names, key=lambda name: order.get(name, len(order))))
        for path, names in faces.items()
        if names
    }


def unknown_people(query: SearchQuery, settings: PeopleSettings) -> str | None:
    """Say, in one line, which `person:` words name nobody.

    Args:
        query: The search.
        settings: `[people]`, with the names.

    Returns:
        The line, or None when every `person:` word names someone.
    """
    names = [folded(person.name) for person in settings.person]
    words = {word for name in names for word in name.split()}
    unknown = [
        term.text
        for term in query.terms
        if term.source is TagSource.PERSON
        and not _known(folded(term.text), (names, words), prefix=term.prefix)
    ]
    if not unknown:
        return None
    return _(
        "Nobody is named {names} yet: name their group on the 'people' page first."
    ).format(names=", ".join(f'"{word}"' for word in unknown))


def _known(text: str, known: tuple[list[str], set[str]], *, prefix: bool) -> bool:
    """Tell whether a typed word names someone.

    Args:
        text: The word or phrase, folded.
        known: The full names and their words, folded.
        prefix: The word ends with a star.

    Returns:
        True for a full name or one of its words (or the start of one).
    """
    names, words = known
    if prefix:
        return any(word.startswith(text) for word in words)
    return text in names or text in words
