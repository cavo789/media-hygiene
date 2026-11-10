"""The lines of *Are my photos safe?* (0689): one source for the home page and `status`.

Each line has a level (green, amber, red, or unknown when the container cannot know),
a title, what it read, and the step of the catalog that fixes it, when one does.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from media_hygiene.cli.status_view import ago
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.safety import BACKUP_FRESH_DAYS, PUSH_FRESH_DAYS
from media_hygiene.services.safety_records import off_pc

if TYPE_CHECKING:
    from media_hygiene.services.safety import SafetyFacts


class Level(StrEnum):
    """How a line reads: green, amber, red, or not known here."""

    GOOD = "good"
    WARN = "warn"
    BAD = "bad"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SafetyLine:
    """One line of the card."""

    level: Level
    title: str
    sub: str
    step: str | None = None  # the catalog's action that fixes it


def copy_line(facts: SafetyFacts) -> SafetyLine:
    """A second copy of the photos: the last complete push, and what is newer.

    Args:
        facts: What the card read.

    Returns:
        The line.
    """
    title = _("A second copy of the photos")
    push = facts.push
    if push is None:
        return SafetyLine(Level.BAD, title, _("mh push never ran."), "push-to")
    when = _("Last push: {ago}.").format(ago=ago(push.started))
    if not push.complete:
        sub = _("{when} It did not finish: run it again.").format(when=when)
        return SafetyLine(Level.WARN, title, sub, "push")
    if facts.newer:
        when += " " + ngettext(
            "{count} file changed since.", "{count} files changed since.", facts.newer
        ).format(count=human_number(facts.newer))
    old = (facts.now - push.started).days >= PUSH_FRESH_DAYS
    return SafetyLine(Level.WARN if old else Level.GOOD, title, when, "push")


def away_line(facts: SafetyFacts) -> SafetyLine:
    """The copy is off this PC: a share or another drive than `C:`.

    Args:
        facts: What the card read.

    Returns:
        The line.
    """
    title = _("The copy is off this PC")
    away = off_pc(facts.push.host if facts.push else None)
    if away is None:
        return SafetyLine(
            Level.UNKNOWN, title, _("Unknown until a push copies a file."), "push-to"
        )
    if not away:
        sub = _("The push target is on C:, the disk of the photos.")
        return SafetyLine(Level.BAD, title, sub, "push-to")
    return SafetyLine(Level.GOOD, title, _("On the NAS or another disk."))


def memory_line(facts: SafetyFacts) -> SafetyLine:
    """The tool's memory: the last `mh backup`, and whether it is off this PC.

    Args:
        facts: What the card read.

    Returns:
        The line.
    """
    title = _("The tool's memory (index, settings, journals)")
    backup = facts.backup
    if backup is None:
        return SafetyLine(Level.BAD, title, _("mh backup never ran."), "backup")
    sub = _("Last backup: {ago}.").format(ago=ago(backup.made))
    old = (facts.now - backup.made).days >= BACKUP_FRESH_DAYS
    if off_pc(backup.host):
        return SafetyLine(Level.WARN if old else Level.GOOD, title, sub, "backup")
    sub += " " + _("It stays on this PC: copy it to a USB stick or the NAS.")
    return SafetyLine(Level.WARN, title, sub, "backup")
