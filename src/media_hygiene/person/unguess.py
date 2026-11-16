"""The cross of a named face on `/person`: no name, confirmed or guessed, in one click.

"This is not Fleur, and I do not want to name it" (the maintainer, 2026-11-16). The
name shown is ruled out (Fleur's `rejected`), and the face is marked `unguessed`: no
other name is guessed for it, where ruling Fleur out alone let the next closest
person be guessed at once. Until then, every name the tool would guess in turn was
ruled out, one person's file each (5 to 13 files per cross on the maintainer's PC),
for names the user never saw. Naming the face later takes both off (`give_name`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.people.changes import Naming, reject_faces
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_ids
from media_hygiene.people.naming import How, id_of, name_all
from media_hygiene.review.slow_log import Laps

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.people.known import Known
    from media_hygiene.person.names import FaceNames

# A confirmed name too: the cross says "not {name}" (2026-11-15: it left ✓ Stéphanie).
_TAKEN_OFF: Final = frozenset({How.CONFIRMED, How.ASSIGNED})


def without_guesses(
    face: StoredFace, known: Known, section: PeopleSettings
) -> tuple[PeopleSettings, tuple[str, ...]]:
    """Rule out the name the tool gives a face, and guess none for it any more.

    Args:
        face: The face of the index.
        known: The references, as the page names the faces now.
        section: `[people]` as written.

    Returns:
        The section to write, and the name ruled out (none when nobody was given).
    """
    named = name_all((face,), known)[0]
    if named.how not in _TAKEN_OFF or not named.name:
        return section, ()
    key = id_of(face)
    ruled = reject_faces(section, Naming(named.name, (key,)))
    marked = (*ruled.unguessed, key) if key not in ruled.unguessed else ruled.unguessed
    return ruled.model_copy(update={"unguessed": marked}), (named.name,)


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
        if key in back.unguessed
        and not any(p.name == name and key in p.faces for p in back.person)
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
    every, laps = names.faces.every, Laps("no name")
    try:
        written = follow_ids(
            read_people(names.config_file), {}, {str(one.path) for one in every}
        )
        laps.lap("read")
        result, ruled = without_guesses(face, names.known(), written)
        laps.lap(f"{len(ruled)} ruled out")
        save_people(names.config_file, result)
        laps.lap("write")
        back = read_people(names.config_file)
        laps.lap("read back")
        laps.said()
    except (ValueError, OSError) as error:
        return {"error": str(error)}
    return {
        "saved": unguessed_line(back, face, ruled),
        "people": [person.name for person in back.person],
    }
