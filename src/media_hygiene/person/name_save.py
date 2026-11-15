"""Save one or several namings of `/person` in one write (2026-11-15).

*Confirm the names guessed: 15* used to send 15 requests, each one reading,
rewriting and reading back every person's file (4 s each on the maintainer's PC):
now the changes are applied one after the other in memory, written once, and read
back once — the proof the page shows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_ids
from media_hygiene.person.one_face_each import section_after
from media_hygiene.review.slow_log import Laps

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.people.roster import Change
    from media_hygiene.person.names import FaceNames


def save_changes(
    names: FaceNames, config_file: Path, changes: Sequence[Change]
) -> PeopleSettings:
    """Apply the changes in order, write `[people]` once, read it back.

    Args:
        names: The page's names and faces.
        config_file: `config.toml`.
        changes: The namings, in the order asked.

    Returns:
        `[people]` as read back from the disk.

    Raises:
        ValueError: A file is not TOML, or the result would not load.
        OSError: A file cannot be read or written.
    """
    who = ", ".join(change.naming.name for change in changes)
    laps = Laps(f"naming {who}")
    original = read_people(config_file)
    laps.lap("read")
    present = {str(face.path) for face in names.faces.every}
    wanted = follow_ids(original, {}, present)
    laps.lap("follow")
    for change in changes:
        wanted = section_after(names, wanted, change)
    laps.lap("change")
    save_people(config_file, wanted)
    laps.lap("write")
    back = read_people(config_file)
    laps.lap("read back")
    laps.said()
    return back
