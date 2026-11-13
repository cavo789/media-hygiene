"""The other lines of *Are my photos safe?* (0689) and the whole card, in order."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.purge_only import nas_only
from media_hygiene.cli.safety_lines import (
    Level,
    SafetyLine,
    away_line,
    copy_line,
    memory_line,
)
from media_hygiene.cli.status_view import ago
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.services.safety import SafetyFacts


def way_back_line(facts: SafetyFacts) -> SafetyLine:
    """The way back: the journals kept, the quarantines mounted.

    Args:
        facts: What the card read.

    Returns:
        The line.
    """
    title = _("The way back (undo)")
    way = facts.way_back
    if not way.journal:
        return SafetyLine(Level.BAD, title, _("The journal is not mounted."))
    if way.lost:
        sub = ngettext(
            "{count} run of the quarantine has lost its journal.",
            "{count} runs of the quarantine have lost their journal.",
            way.lost,
        ).format(count=way.lost)
        return SafetyLine(Level.BAD, title, sub, "history")
    if way.unplugged:
        sub = _("Quarantine not mounted: {drives}.").format(
            drives=", ".join(way.unplugged)
        )
        return SafetyLine(Level.WARN, title, sub, "history")
    return SafetyLine(
        Level.GOOD, title, _("Every journal is there, every quarantine mounted.")
    )


def quarantine_line(facts: SafetyFacts, purge_days: int) -> SafetyLine:
    """What waits in the quarantine, and how much of it exists nowhere else.

    Args:
        facts: What the card read.
        purge_days: `[clean] purge_hint_days`: older is said amber.

    Returns:
        The line.
    """
    title = _("Waiting in the quarantine")
    held = facts.quarantine
    if not held.runs:
        return SafetyLine(Level.GOOD, title, _("Empty."))
    oldest = min(run.started for run in held.runs)
    sub = _("{size}, the oldest set aside {ago}.").format(
        size=human_size(held.size), ago=ago(oldest)
    )
    if facts.only:
        sub += " " + ngettext(
            "{count} file exists nowhere else.",
            "{count} files exist nowhere else.",
            facts.only,
        ).format(count=human_number(facts.only))
    if facts.nas:
        sub += " " + nas_only(facts.nas)
    old = (facts.now - oldest).days >= purge_days
    return SafetyLine(Level.WARN if old else Level.GOOD, title, sub, "purge")


def damaged_line(facts: SafetyFacts) -> SafetyLine:
    """The files the re-read found damaged (0690).

    Args:
        facts: What the card read.

    Returns:
        The line.
    """
    title = _("Damaged files")
    counts = facts.reread
    if counts is None or not counts.read:
        return SafetyLine(Level.UNKNOWN, title, _("Not known before a re-read."))
    if counts.damaged:
        sub = ngettext(
            "{count} file found damaged: mh clean --repair puts its copy back.",
            "{count} files found damaged: mh clean --repair puts their copy back.",
            counts.damaged,
        ).format(count=human_number(counts.damaged))
        return SafetyLine(Level.BAD, title, sub)
    return SafetyLine(Level.GOOD, title, _("None found."))


def reread_line(facts: SafetyFacts) -> SafetyLine:
    """How far the re-read went: the files read again in full at least once.

    Args:
        facts: What the card read.

    Returns:
        The line.
    """
    title = _("Files read again in full")
    counts = facts.reread
    if counts is None or not counts.files:
        return SafetyLine(Level.UNKNOWN, title, _("No index yet: run an audit."))
    if not counts.read:
        return SafetyLine(Level.WARN, title, _("Never: mh upkeep does it."), "upkeep")
    sub = _("{read} of {files} files ({percent} %).").format(
        read=human_number(counts.read),
        files=human_number(counts.files),
        percent=min(100, counts.read * 100 // counts.files),
    )
    return SafetyLine(Level.GOOD, title, sub, "upkeep")


def drill_line() -> SafetyLine:
    """The restore drill: not offered yet (it needs `mh pull`, 0436).

    Returns:
        The line, never tried.
    """
    return SafetyLine(
        Level.UNKNOWN,
        _("A restore tried"),
        _("Never tried: a restore test from the NAS comes with mh pull."),
    )


def safety_card(facts: SafetyFacts, purge_days: int) -> tuple[SafetyLine, ...]:
    """Every line of the card, in order.

    Args:
        facts: What the card read.
        purge_days: `[clean] purge_hint_days`.

    Returns:
        The lines.
    """
    return (
        copy_line(facts),
        away_line(facts),
        memory_line(facts),
        way_back_line(facts),
        quarantine_line(facts, purge_days),
        damaged_line(facts),
        reread_line(facts),
        drill_line(),
    )
