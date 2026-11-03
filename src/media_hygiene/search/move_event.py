"""The event *Move to an event…* remembers (0556): its name, its period, its cameras.

A move writes (or extends) one `date_range` rule in `events/<year>.toml` (0576): the
event's name as its category, the days of the files moved as its period, their cameras
as `devices`. No list of files: they are those of the event's folder (`event_folder`
finds it again when renamed). Which event a move joins: `event_match`. The dialog says
before the move what will be remembered (`foreseen`), after it what the file holds
(`remember_event`). Camera serial numbers are not read: the index keeps make and model
only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.classify.event_store import add_event
from media_hygiene.classify.rules_edit import replace_rule
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _, ngettext
from media_hygiene.search.event_match import (
    events_named,
    joined_event,
    label,
    new_event,
    widened,
    with_month,
)

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Collection
    from pathlib import Path

    from media_hygiene.search.event_match import Moved
    from media_hygiene.services.selection_models import MoveView

_CAMERA: Final = "SELECT camera FROM files WHERE rowid = ?"


def cameras_of(
    connection: sqlite3.Connection, keys: Collection[int]
) -> tuple[str, ...]:
    """The cameras of the files moved, as the index reads them from EXIF.

    Args:
        connection: The index.
        keys: The keys moved.

    Returns:
        Each camera once, sorted; none for files without one (received, scans).
    """
    found = {
        str(row[0]).strip()
        for key in keys
        if (row := connection.execute(_CAMERA, (key,)).fetchone()) and row[0]
    }
    return tuple(sorted(camera for camera in found if camera))


def foreseen(config_file: Path, moved: Moved) -> str:
    """Say, before the move, which event it will be remembered as.

    Args:
        config_file: `config.toml`.
        moved: The move.

    Returns:
        The sentence; empty without a name or a date.
    """
    if not moved.name or not moved.days:
        return ""
    try:
        rules = read_rules(config_file)
    except ConfigError, ValueError:
        return ""
    events = events_named(rules, moved.name)
    joined = joined_event(events, moved)
    if joined is not None:
        said = _("It will be remembered in the event '{name}' (events/).")
        return said.format(name=label(joined, rules))
    if events:
        said = _("It will be remembered as a new '{name}': '{other}' is another event.")
        return said.format(name=moved.name, other=with_month(events[0]))
    said = _("It will be remembered as the event '{name}' (events/).")
    return said.format(name=moved.name)


def remember_event(config_file: Path, moved: Moved) -> str:
    """Write or extend the event of a move, read it back and say it.

    Args:
        config_file: `config.toml`.
        moved: The move.

    Returns:
        The sentence to show; empty when no file has a date.
    """
    if not moved.days:
        return ""
    try:
        events = events_named(read_rules(config_file), moved.name)
        joined = joined_event(events, moved)
        if joined is None:
            held = add_event(config_file, new_event(events, moved))
        else:
            held = replace_rule(config_file, joined.name, widened(joined, moved))
        rules = read_rules(config_file)
    except (ConfigError, ValueError) as exc:
        return _("The event is not remembered: {reason}").format(reason=exc)
    said = _("The event '{name}' is remembered: {dates}.")
    said = said.format(name=label(held, rules), dates=held.dates)
    return said + _devices_said(held.devices)


def _devices_said(devices: tuple[str, ...]) -> str:
    """The cameras remembered, or that none tells the event's photos apart.

    Args:
        devices: The event's cameras.

    Returns:
        The sentence, a space before it.
    """
    if devices:
        return " " + _("Cameras: {cameras}.").format(cameras=", ".join(devices))
    return " " + _("No camera in these files: a late photo will be asked.")


def goes_said(view: MoveView) -> str:
    r"""Where the files ticked go, in one sentence (0574): what *Sort here now* does.

    Args:
        view: Where the photos picked would go.

    Returns:
        "These 10 files will go to C:\Photos\…"; without a destination or a file
        ticked, that nothing is proposed.
    """
    files = sum(source.files for source in view.sources if source.ticked)
    if not view.target or not files:
        return _(
            "No folder is proposed for these files: choose one with Another folder…."
        )
    said = ngettext(
        "This file will go to {folder}.", "These {n} files will go to {folder}.", files
    )
    return said.format(n=files, folder=view.target)
