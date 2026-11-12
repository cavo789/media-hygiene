"""`POST /person/api/forget`: a face drawn by hand by mistake, or twice, forgotten.

Only a face drawn on the page (`drawn_faces`, 0715) can be: a face the audit found
would come back at the next audit, so the page never offers it. Its id first leaves
the names (confirmed, ruled out, ignored), read back from `config.toml`; then its row
leaves the index, read back too: the page says what the index holds now. Names that
cannot be written leave the face as it was: a face drawn later on the same photo may
get the same number, and must not inherit a name.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.i18n import _, ngettext
from media_hygiene.index.drawn_faces import forget_drawn, is_drawn
from media_hygiene.index.repository import FactsRepository
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.naming import face_id, id_of

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.person.finding import PersonFinder
    from media_hygiene.person.names import FaceNames


class ForgetAsked(BaseModel):
    """A face of the page, by its shelf number."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: int = Field(ge=0)


def without_ids(section: PeopleSettings, ids: frozenset[str]) -> PeopleSettings:
    """The names without some faces: neither confirmed, nor ruled out, nor ignored.

    Args:
        section: `[people]` as written.
        ids: The faces, by id.

    Returns:
        The section to write; a person left without any face is dropped, as after
        every change of the people page (`changes`).
    """
    people = tuple(
        person.model_copy(
            update={
                "faces": tuple(key for key in person.faces if key not in ids),
                "rejected": tuple(key for key in person.rejected if key not in ids),
            }
        )
        for person in section.person
    )
    return section.model_copy(
        update={
            "person": tuple(person for person in people if person.faces),
            "ignored": tuple(key for key in section.ignored if key not in ids),
        }
    )


def _named(section: PeopleSettings, wanted: str) -> bool:
    """Tell whether the names mention a face.

    Args:
        section: `[people]`.
        wanted: The face's id.

    Returns:
        True when someone has it, rules it out, or it is ignored.
    """
    return wanted in section.ignored or any(
        wanted in person.faces or wanted in person.rejected for person in section.person
    )


def _unnamed(names: FaceNames | None, wanted: str) -> str | None:
    """Take a face out of the names of `config.toml`, read back.

    Args:
        names: The names desk; None: no name is known on this page.
        wanted: The face's id.

    Returns:
        None once the file no longer names it (or never did); else why not.
    """
    if names is None or not _named(names.settings(), wanted):
        return None
    if names.config_file is None:
        return _("names are kept in config.toml: mount a folder of yours on /config")
    try:
        written = read_people(names.config_file)
        save_people(names.config_file, without_ids(written, frozenset({wanted})))
        back = read_people(names.config_file)
    except (ValueError, OSError) as error:
        return str(error)
    if _named(back, wanted):
        return _("config.toml still names this face.")
    return None


def forgotten(finder: PersonFinder, body: bytes) -> dict[str, object]:
    """Forget a face drawn by hand: its names, then its row of the index.

    Args:
        finder: The page's faces, index and names.
        body: A `ForgetAsked`, as JSON.

    Returns:
        `saved`: what the index holds now for the photo; or `error`.

    Raises:
        ValidationError: The body is not a face.
    """
    asked = ForgetAsked.model_validate_json(body)
    face = finder.shelf.face(str(asked.key))
    index = finder.faces
    drawn = face is not None and face.number is not None and is_drawn(face.number)
    if face is None or face.number is None or not drawn or index.file is None:
        return {"error": _("Only a face drawn by hand can be forgotten here.")}
    wanted = face_id(face.path, face.number)
    error = _unnamed(finder.names, wanted)
    if error is not None:
        return {"error": error}
    try:
        with FactsRepository.open(index.file) as repository:
            forget_drawn(repository.connection, index.model, (face.path, face.number))
    except sqlite3.Error as failure:
        return {"error": str(failure)}
    index.refresh()
    left = index.of(face.path)
    if any(id_of(one) == wanted for one in left):
        return {"error": _("The index still holds this face.")}
    said = ngettext(
        "Face forgotten, read back from the index: this photo has {n} face now.",
        "Face forgotten, read back from the index: this photo has {n} faces now.",
        len(left),
    )
    return {"saved": said.format(n=len(left))}
