"""The cross of a named face on `/person`: no name, confirmed or guessed, in one click.

Ruling out the name guessed lets the next closest person be guessed, then the next:
the user would click once per name. Here every name the tool would guess in turn is
ruled out (`rejected` of each person, the format the people page already writes),
until the face is nobody's; one save, read back. Naming the face later takes it out
of that person's `rejected`, as always (`give_name`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.people.changes import Naming, reject_faces
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_ids
from media_hygiene.people.known import Known
from media_hygiene.people.naming import How, id_of, name_all

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.person.names import FaceNames

# A confirmed name too: the cross says "not {name}" (2026-11-15: it left ✓ Stéphanie).
_TAKEN_OFF: Final = frozenset({How.CONFIRMED, How.ASSIGNED})


def without_guesses(
    face: StoredFace, every: Sequence[StoredFace], section: PeopleSettings
) -> tuple[PeopleSettings, tuple[str, ...]]:
    """Rule out each name the tool would give a face, until it gives none.

    Args:
        face: The face of the index.
        every: Every face of the index (the references among them).
        section: `[people]`, the thresholds of the run with the names as written.

    Returns:
        The section to write, and the names ruled out, in the order they were guessed.
    """
    ruled: list[str] = []
    for _person in range(len(section.person)):  # each person is ruled out once at most
        named = name_all((face,), Known.of(every, section))[0]
        if named.how not in _TAKEN_OFF or not named.name:
            break
        ruled.append(named.name)
        section = reject_faces(section, Naming(named.name, (id_of(face),)))
    return section, tuple(ruled)


def unguessed_line(back: PeopleSettings, face: StoredFace, ruled: Sequence[str]) -> str:
    """Say what `config.toml` holds now for the face.

    A person whose only face was this one leaves the file with its `rejected`: the
    name is checked gone from the face, not ruled out.

    Args:
        back: `[people]` read back from the disk.
        face: The face.
        ruled: The names taken off it.

    Returns:
        The names the face no longer bears, or that nothing changed.
    """
    key = id_of(face)
    gone = [
        name
        for name in ruled
        if not any(p.name == name and key in p.faces for p in back.person)
    ]
    if not gone:
        return _("Not saved: config.toml rules out no name for this face.")
    return _(
        "Saved in config.toml, read back: this face is not {names}; it stays to name."
    ).format(names=", ".join(gone))


def unname(names: FaceNames, key: int) -> dict[str, object]:
    """Take every guessed name off a face of the page, saved, read back.

    Args:
        names: The page's names (`config.toml` writable: checked by the caller).
        key: The face's shelf number.

    Returns:
        The line read back (`saved`) and the names known; or `error`.
    """
    face = names.stored(key)
    if face is None or names.config_file is None:
        return {"error": _("This face was found by a second look: it cannot be named.")}
    every = names.faces.every
    try:
        written = follow_ids(
            read_people(names.config_file), {}, {str(one.path) for one in every}
        )
        merged = names.settings().model_copy(update={"person": written.person})
        result, ruled = without_guesses(face, every, merged)
        save_people(
            names.config_file, written.model_copy(update={"person": result.person})
        )
        back = read_people(names.config_file)
    except (ValueError, OSError) as error:
        return {"error": str(error)}
    return {
        "saved": unguessed_line(back, face, ruled),
        "people": [person.name for person in back.person],
    }
