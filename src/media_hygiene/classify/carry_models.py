"""What a `classify` run carried over from the previous workbook, kept in `plan.json`.

The report and the console read it: how many edits were carried, from which workbook,
which events were split, and every edit that found no target (never dropped silently).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class EditSheet(StrEnum):
    """The sheet an edit was typed on."""

    FILES = "files"
    EVENTS = "events"
    CATEGORIES = "categories"


class LostWhy(StrEnum):
    """Why an edit could not be carried over."""

    GONE = "gone"  # its file, event or category is no longer in the proposal
    INVALID = "invalid"  # the value cannot be used (a name Windows refuses…)
    MERGED = "merged"  # its event merged into another named event, which wins
    CONFLICT = "conflict"  # chosen in the review page, edited otherwise in the workbook


class LostEdit(BaseModel):
    """One edit that was not carried over, as the user typed it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sheet: EditSheet
    key: str  # the file (host path or row id), the event, the category
    value: str  # what was typed: a folder, a name, a note…
    why: LostWhy


class CarryRecord(BaseModel):
    """Where the carried edits come from, and what could not be carried."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workbook: str  # host path of the workbook read
    saved_at: str  # ISO date and time it was saved, local
    edits: int  # the edits carried over (files, events, categories)
    notes: int = 0  # the notes carried over
    split: tuple[str, ...] = ()  # the events whose edit went to several events
    lost: tuple[LostEdit, ...] = ()
