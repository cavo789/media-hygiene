"""Carry the event edits and notes of the previous workbook to the new events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.carry_events import EventMatch, event_targets
from media_hygiene.classify.carry_models import EditSheet, LostEdit, LostWhy
from media_hygiene.classify.carry_types import typed_text

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.classify.carry_events import Targets
    from media_hygiene.classify.carry_types import CarrySource
    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.classify.workbook.edits import EventEdit


@dataclass(frozen=True, slots=True)
class EventsCarried:
    """The event edits and notes by new event id, the events split, those lost."""

    edits: dict[str, EventEdit]
    notes: dict[str, str]
    split: tuple[str, ...]
    lost: tuple[LostEdit, ...]


def carry_events(
    source: CarrySource, new: ClassifyPlan, rows: Mapping[str, str]
) -> EventsCarried:
    """Carry the event edits and notes.

    Args:
        source: The previous workbook.
        new: The new plan.
        rows: Previous row id → new row id.

    Returns:
        What was carried, and what was not.
    """
    return _EventCarrier(source, new, rows).run()


class _EventCarrier:
    """Carries the edits of the Events sheet, listing those left behind."""

    def __init__(
        self, source: CarrySource, new: ClassifyPlan, rows: Mapping[str, str]
    ) -> None:
        """Keep both plans and the rows matched.

        Args:
            source: The previous workbook.
            new: The new plan.
            rows: Previous row id → new row id.
        """
        self._source, self._new, self._rows = source, new, rows
        self._lost: list[LostEdit] = []

    def run(self) -> EventsCarried:
        """Carry the event edits and notes to the new events holding their files.

        Returns:
            The edits and the notes by new event id, the events split, the lost.
        """
        salvaged = self._source.salvaged
        edits, notes = salvaged.edits.events, salvaged.notes.events
        targets, merged = self._targets()
        carried: tuple[dict[str, EventEdit], dict[str, str]] = ({}, {})
        split: list[str] = []
        for key in sorted(targets):
            chosen, edit = targets[key], edits.get(key)
            if chosen is None:  # a sort applied it to all its files
                continue
            if not chosen:
                self._lose_event(key, (edit, notes.get(key)), merged=key in merged)
                continue
            if edit is not None and len(chosen) > 1:
                split.append(edit.name or self._event_name(key))
            for event_id in chosen:
                _put(carried, event_id, (edit, notes.get(key)))
        return EventsCarried(*carried, tuple(split), tuple(self._lost))

    def _targets(self) -> tuple[Targets, frozenset[str]]:
        """The new events of every previous event holding an edit or a note.

        Notes never take an event away from an edit: they are matched apart.

        Returns:
            Previous event → new events, and the previous events merged away.
        """
        source = self._source
        edits, notes = source.salvaged.edits.events, source.salvaged.notes.events
        match = EventMatch(source.plan, self._new, self._rows, source.applied)
        targets, merged = event_targets(sorted(edits), match)
        alone, merged_alone = event_targets(sorted(set(notes) - set(edits)), match)
        return targets | alone, merged | merged_alone

    def _lose_event(
        self, key: str, typed: tuple[EventEdit | None, str | None], *, merged: bool
    ) -> None:
        """List the edit and the note of an event that found no new event.

        Args:
            key: The previous event id.
            typed: Its edit and its note.
            merged: Its files joined an event another edit won.
        """
        edit, note = typed
        name = self._event_name(key)
        why = LostWhy.MERGED if merged else LostWhy.GONE
        for value in (edit.name or edit.category if edit else None, note):
            if value:
                self._lost.append(
                    LostEdit(
                        sheet=EditSheet.EVENTS,
                        key=name,
                        value=typed_text(value),
                        why=why,
                    )
                )

    def _event_name(self, key: str) -> str:
        """The name of a previous event, as the report showed it.

        Args:
            key: Its id.

        Returns:
            Its label or dates, else its id.
        """
        old = self._source.plan
        event = next((e for e in old.events if e.id == key), None) if old else None
        return (event.label or event.span) if event else key


def _put(
    carried: tuple[dict[str, EventEdit], dict[str, str]],
    event_id: str,
    typed: tuple[EventEdit | None, str | None],
) -> None:
    """Give a new event the edit and the note of a previous one.

    Args:
        carried: The edits and the notes carried so far.
        event_id: The new event.
        typed: The edit and the note; notes of two events are joined.
    """
    edits, notes = carried
    edit, note = typed
    if edit is not None:
        edits[event_id] = edit
    if note:
        notes[event_id] = " / ".join(filter(None, (notes.get(event_id), note)))
