"""Move faces from one person to another: "not Chloé, it is Manon" (TODO 0712).

One change instead of two: the faces are confirmed as the new person's (taken from
anyone else, as `give_name` does) and ruled out of the person they were shown under,
so that the nearest-face naming never gives them back. Shared by the people page and
the page of one person (`/person`, TODO 0714).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.people.changes import Naming, give_name, reject_faces

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings


def move_faces(section: PeopleSettings, naming: Naming, source: str) -> PeopleSettings:
    """Give faces a name and rule them out of the person they were shown under.

    Args:
        section: `[people]` as written.
        naming: The new name and the faces.
        source: The name they were shown under; empty for an unnamed group.

    Returns:
        The section to write.
    """
    named = give_name(section, Naming(naming.name, naming.faces))
    if (
        not source.strip()
        or source.strip().casefold() == naming.name.strip().casefold()
    ):
        return named
    return reject_faces(named, Naming(source, naming.faces))
