"""The steps of the three quick guides, as the `mh` menu lists them.

The order is the guides' (`documentation/*/{clean,sort,find}/quick-guide.md`), the
badges theirs: 🔒 photos untouched, ↩️ can be undone, ⚠️ for good.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from media_hygiene.cli.status_step import Slot
from media_hygiene.i18n import _


class Risk(StrEnum):
    """What a step may do to the photos, as the guides badge it."""

    SAFE = "🔒"
    UNDO = "↩️"
    FINAL = "⚠️"


@dataclass(frozen=True, slots=True)
class Step:
    """A step of a guide: its command, what it does, what it risks."""

    command: str  # without `mh`; empty: the user types it (`typed` shows how)
    text: str
    risk: Risk
    slot: Slot | None = None
    optional: bool = False
    ai: bool = False  # may ask the local model of `[classify.ai]` 🤖
    typed: str = ""  # the command to type, for a step the menu cannot fill


def clean_steps() -> tuple[Step, ...]:
    """The steps of "Clean in short".

    Returns:
        Them, in order.
    """
    return (
        Step(
            "audit",
            _("Find the duplicates and the broken files"),
            Risk.SAFE,
            Slot.AUDIT,
        ),
        Step(
            "clean", _("Set the extra copies aside (asks first)"), Risk.UNDO, Slot.CLEAN
        ),
        Step("history", _("What each run did"), Risk.SAFE),
        Step("undo", _("Put back the files of the last run"), Risk.UNDO, Slot.UNDO),
        Step(
            "review",
            _("Choose the best shots of each burst, in your browser"),
            Risk.SAFE,
            Slot.REVIEW,
            optional=True,
        ),
        Step(
            "clean --tier near --decisions",
            _("Apply your choices: what you set aside goes to the quarantine"),
            Risk.UNDO,
            Slot.APPLY,
            optional=True,
        ),
        Step(
            "purge",
            _("Free the space of the quarantine, for good"),
            Risk.FINAL,
            Slot.PURGE,
        ),
    )


def sort_steps() -> tuple[Step, ...]:
    """The steps of "Sort in short".

    Returns:
        Them, in order.
    """
    return (
        Step(
            "classify",
            _("Propose a tidy tree, in a workbook you correct"),
            Risk.SAFE,
            Slot.CLASSIFY,
            ai=True,
        ),
        Step(
            "review-sort",
            _("Name the events in your browser"),
            Risk.SAFE,
            optional=True,
        ),
        Step("places", _("Name your places on a map"), Risk.SAFE, optional=True),
        Step(
            "people",
            _("Name the faces"),
            Risk.SAFE,
            Slot.PEOPLE,
            optional=True,
        ),
        Step("sort", _("Move the photos as the workbook says"), Risk.UNDO, Slot.SORT),
        Step(
            "",
            _("Gather a selection into an album of links"),
            Risk.UNDO,
            optional=True,
            typed='album "Christmas" --category …',
        ),
    )


def find_steps() -> tuple[Step, ...]:
    """The steps of "Find in short".

    Returns:
        Them, in order.
    """
    return (
        Step("tags", _("Give your photos words"), Risk.SAFE, Slot.TAGS, ai=True),
        Step("search", _("Find a photo by its words, in your browser"), Risk.SAFE),
        Step(
            "xmp",
            _("Carry the words into other photo software"),
            Risk.UNDO,
            optional=True,
        ),
        Step(
            "inventory",
            _("Every photo and video in an Excel workbook"),
            Risk.SAFE,
            optional=True,
        ),
    )
