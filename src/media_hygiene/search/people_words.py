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
from media_hygiene.people.folding import folded
from media_hygiene.people.naming import Known, name_all
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
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
    if not settings.person:
        return {}
    try:
        faces = FaceStore(connection, FACE_MODEL).faces()
    except sqlite3.OperationalError:  # no `faces` table: `people` never ran
        return {}
    order = {person.name: rank for rank, person in enumerate(settings.person)}
    found: dict[Path, set[str]] = {}
    for face, name in zip(
        faces, name_all(faces, Known.of(faces, settings)), strict=True
    ):
        if name.named:
            found.setdefault(face.path, set()).add(name.name)
    return {
        path: tuple(sorted(names, key=lambda name: order.get(name, len(order))))
        for path, names in found.items()
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
