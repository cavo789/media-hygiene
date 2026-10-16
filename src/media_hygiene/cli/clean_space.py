"""Before `clean` asks: the copies to another drive, refused when they don't fit.

Said only for a drive without a quarantine of its own (`/quarantine/<x>`, 0183): with
one, its files stay on it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.errors import MountError
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.quarantine_space import (
    cross_drive,
    quarantine_route,
    set_aside,
)

if TYPE_CHECKING:
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.services.quarantine_space import Room
    from media_hygiene.services.runtime import Runtime


def check_quarantine_room(runtime: Runtime, plan: CleanPlan) -> None:
    """Say which files are copied to another drive; refuse when they don't fit there.

    Runs before the confirmation, hence before any move or journal entry.

    Args:
        runtime: Settings, mount points and output.
        plan: What would be cleaned.

    Raises:
        MountError: The quarantine's drive lacks the room, the headroom kept.
    """
    headroom = runtime.settings.clean.quarantine_headroom
    rooms = cross_drive(quarantine_route(runtime), set_aside(plan), headroom)
    for room in rooms:
        if room.missing:
            raise MountError(_refusal(room), _tip(room))
    for room in rooms:
        runtime.output.warning(_line(room))


def _line(room: Room) -> str:
    """The warning: how much is copied from which drive, and the room left.

    Args:
        room: What a quarantine receives from other drives.

    Returns:
        E.g. "12 files (3.1 GB) will be copied from E: to the quarantine on C:
        (40.2 GB free there)."
    """
    cross = room.cross
    line = ngettext(
        "{count} file ({size}) will be copied from {sources} to the quarantine "
        "on {drive} ({free} free there).",
        "{count} files ({size}) will be copied from {sources} to the quarantine "
        "on {drive} ({free} free there).",
        cross.count,
    )
    return line.format(
        count=human_number(cross.count),
        size=human_size(cross.size),
        sources=", ".join(cross.sources),
        drive=cross.drive,
        free=human_size(room.free),
    )


def _refusal(room: Room) -> str:
    """The refusal: the copies would not fit on the quarantine's drive.

    Args:
        room: What a quarantine receives from other drives.

    Returns:
        The message, with how much is missing.
    """
    cross = room.cross
    message = ngettext(
        "Not enough room on {drive} for the quarantine: {count} file ({size}) "
        "would be copied there from {sources}, {free} free; {missing} missing "
        "({headroom} stay free). Nothing was changed.",
        "Not enough room on {drive} for the quarantine: {count} files ({size}) "
        "would be copied there from {sources}, {free} free; {missing} missing "
        "({headroom} stay free). Nothing was changed.",
        cross.count,
    )
    return message.format(
        drive=cross.drive,
        count=human_number(cross.count),
        size=human_size(cross.size),
        sources=", ".join(cross.sources),
        free=human_size(room.free),
        missing=human_size(room.missing),
        headroom=human_size(room.headroom),
    )


def _tip(room: Room) -> str:
    """How to make room: free the drive, or give the photos' drive its own quarantine.

    Args:
        room: What a quarantine receives from other drives.

    Returns:
        The tip: `mh` mounts one for each drive of its photo folders (0183).
    """
    source = room.cross.sources[0]
    return _(
        "Free space on {drive} ('purge' erases the files of earlier cleans), or "
        "give {source} its own quarantine: 'mh folders add' with a folder of "
        '{source}, or -v "{source}\\media-hygiene\\quarantine:/quarantine/{letter}".'
    ).format(drive=room.cross.drive, source=source, letter=source[0].lower())
