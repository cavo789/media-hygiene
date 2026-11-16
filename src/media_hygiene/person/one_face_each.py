"""A person is on a photo once: naming a face takes that name off the photo's others.

Two faces of one photo named the same are a mistake (two people of the same name are
told apart by the user: "Stéphanie 1", "Stéphanie 2"). When a face is named, every other
face of its photo that is confirmed as that person, or guessed so, is ruled out for that
name (`rejected`, as the people page writes it), in the same save (2026-11-15).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.people.changes import Naming, give_name, reject_faces
from media_hygiene.people.known import Known
from media_hygiene.people.moving import move_faces
from media_hygiene.people.naming import How, id_of, name_all

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.people.roster import Change
    from media_hygiene.person.names import FaceNames

_NAMED: Final = frozenset({How.CONFIRMED, How.ASSIGNED})


def alone_on_its_photos(
    names: FaceNames, wanted: PeopleSettings, naming: Naming
) -> PeopleSettings:
    """Rule the name out for the other faces of the photos of the faces named.

    Args:
        names: The page's names and faces.
        wanted: `[people]` with the naming applied, to write.
        naming: The name and the faces given it.

    Returns:
        The section to write; unchanged when no other face of the photos bears the name.
    """
    named = frozenset(naming.faces)
    paths = {face.path for face in names.faces.every if id_of(face) in named}
    others = tuple(
        face
        for path in paths
        for face in names.faces.of(path)
        if id_of(face) not in named
    )
    if not others:
        return wanted
    every = names.faces.every
    merged = names.settings().model_copy(update={"person": wanted.person})
    given = name_all(others, Known.of(every, merged))
    twins = tuple(
        id_of(face)
        for face, name in zip(others, given, strict=True)
        if name.how in _NAMED and name.name == naming.name
    )
    return reject_faces(wanted, Naming(naming.name, twins)) if twins else wanted


def section_after(
    names: FaceNames, written: PeopleSettings, change: Change
) -> PeopleSettings:
    """The section to write: the change asked, then the name once on each photo.

    Args:
        names: The page's names and faces.
        written: `[people]` as the file holds it.
        change: The action, the naming and its source.

    Returns:
        The section to write.
    """
    if change.action == "reject":
        return reject_faces(written, change.naming)
    if change.action == "move":
        wanted = move_faces(written, change.naming, change.source)
    else:
        wanted = give_name(written, change.naming)
    return alone_on_its_photos(names, wanted, change.naming)
