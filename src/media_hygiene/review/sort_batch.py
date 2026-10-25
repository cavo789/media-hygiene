"""The sure proposals of the sort review, accepted or taken back in one write.

The page asks for the events whose proposal is sure (`sort_sure`); each one still open
(nothing chosen here nor in the workbook) is recorded as Enter would record it, with
the workbook's value it saw as `base`. The file is then read back from the disk: the
page shows what the disk holds, never what was meant to be written.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.page_decisions import (
    EventDecision,
    read_page_decisions,
    write_page_decisions,
)
from media_hygiene.classify.page_values import EventValue
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.review.sort_choosing import SortChoosing
from media_hygiene.review.sort_session import now
from media_hygiene.review.sort_sure import sure_value
from media_hygiene.review.sort_views import CardMaker, EventCard

if TYPE_CHECKING:
    from collections.abc import Mapping

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_NANOSECONDS: Final = 1_000_000_000


class SureBatch(BaseModel):
    """`POST /api/sure`: the events whose sure proposal is accepted, or taken back."""

    model_config = _FROZEN

    events: tuple[str, ...]
    undo: bool = False


class BatchAnswer(BaseModel):
    """What the decisions file holds of a batch, as read back from the disk."""

    model_config = _FROZEN

    changed: int  # events accepted, or taken back
    size: int  # of the decisions file, in bytes
    modified: str  # ISO 8601, UTC: the page shows it in local time
    events: tuple[EventCard, ...]  # the events of the batch, as chosen now


class SortBatchSession(SortChoosing):
    """The sort review, and the batch of its sure proposals."""

    def open_and_sure(self) -> tuple[int, int]:
        """Count the events still to decide, and those one click may accept.

        Returns:
            The events still to decide, then the sure ones among them.
        """
        open_events = [
            item
            for item in self._work.values()
            if item.undecided and self._open(item.event.id)
        ]
        sure = sum(1 for item in open_events if sure_value(item) is not None)
        return len(open_events), sure

    def batch(self, request: SureBatch) -> BatchAnswer:
        """Accept the sure proposals of events still open, or take them back; save once.

        Args:
            request: The events, and which way.

        Returns:
            The batch, read back from the disk.

        Raises:
            DecisionsError: Nothing to accept or to take back, or the file read back
                does not hold the batch.
            OSError: The file could not be written; the choices stay as they were.
        """
        events = dict(self._events)
        changed: dict[str, EventDecision] = {}
        for event_id in dict.fromkeys(request.events):
            item = self._work.get(event_id)
            value = None if item is None else sure_value(item)
            if value is None:
                continue
            if request.undo and _accepted(events.get(event_id), value):
                changed[event_id] = events.pop(event_id)
            elif not request.undo and self._open(event_id):
                decision = EventDecision(
                    event=event_id, value=value, base=EventValue(), saved=now()
                )
                changed[event_id] = events[event_id] = decision
        if not changed:
            raise DecisionsError(
                _("Nothing to take back.")
                if request.undo
                else _("No sure proposal left to accept.")
            )
        previous, self._events = self._events, events
        try:
            write_page_decisions(self._source.target, self.decisions())
        except OSError:
            self._events = previous
            raise
        return self._read_back(changed, undo=request.undo)

    def _open(self, event_id: str) -> bool:
        """Tell whether nothing is chosen for an event, here or in the workbook.

        Args:
            event_id: The event.

        Returns:
            True when it is still to decide.
        """
        workbook = EventValue.of(self._source.workbook.events.get(event_id))
        return event_id not in self._events and workbook.empty

    def _read_back(
        self, changed: Mapping[str, EventDecision], *, undo: bool
    ) -> BatchAnswer:
        """Read the decisions file again and check that it holds the batch.

        Args:
            changed: The events of the batch, with the choice accepted or taken back.
            undo: Whether the batch took them back.

        Returns:
            The answer, from the disk.

        Raises:
            DecisionsError: The file does not hold the batch.
        """
        target = self._source.target
        disk = read_page_decisions(target, self._source.plan.plan_id)
        held = {item.event: item for item in disk.events}
        missing = [
            event_id
            for event_id, decision in changed.items()
            if (held.get(event_id) is None) != undo
            or (not undo and held[event_id] != decision)
        ]
        if missing:
            message = _(
                "{path} read back does not hold the {count} choices just saved."
            )
            raise DecisionsError(message.format(path=target.name, count=len(missing)))
        written = target.stat()
        modified = datetime.fromtimestamp(written.st_mtime_ns / _NANOSECONDS, tz=UTC)
        cards = CardMaker(self._source.workbook, held, self._files, self._moved)
        return BatchAnswer(
            changed=len(changed),
            size=written.st_size,
            modified=modified.isoformat(),
            events=tuple(cards.event(self._work[event_id]) for event_id in changed),
        )


def _accepted(decision: EventDecision | None, value: EventValue) -> bool:
    """Tell whether an event's choice is its sure proposal, as a batch accepted it.

    Args:
        decision: The page's choice of the event, if any.
        value: Its sure proposal.

    Returns:
        True when taking the batch back may forget it: a choice made since stays.
    """
    return decision is not None and decision.value == value and decision.base.empty
