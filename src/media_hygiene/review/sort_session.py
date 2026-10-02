"""A sort review in progress: the page's choices, saved after every one of them.

The choices lie in `sort-decisions.json`, next to `plan.json`; each one records what
the workbook said when it was made (`base`), so that `sort` sees a later workbook
edit of the same event or file. Reopened on the same plan, the review resumes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.page_decisions import (
    EventDecision,
    PageDecisions,
    write_page_decisions,
)
from media_hygiene.classify.page_values import EventValue
from media_hygiene.classify.worklist import work_list
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.review.sort_files import file_decisions, movable_rows
from media_hygiene.review.sort_state import EventView, SortState, categories_used
from media_hygiene.review.sort_views import CardMaker

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.worklist import WorkItem
    from media_hygiene.review.sort_files import SendFiles, SortSource


class SortSession:
    """The events under review and the page's choices, in memory and on disk."""

    def __init__(self, source: SortSource, base: PageDecisions) -> None:
        """Resume the choices of `base` whose event or file is still in the plan.

        Args:
            source: The plan, the workbook's edits, the decisions file.
            base: What the decisions file holds already.
        """
        self._source = source
        self._work = {item.event.id: item for item in work_list(source.plan)}
        self._rows = {row.id: row for row in source.plan.rows}
        self._events = {item.event: item for item in base.events}
        self._files = {item.row: item for item in base.files}
        self.hosts = source.hosts  # the workbook and the decisions file, on the host

    @property
    def event_count(self) -> int:
        """The number of events of the work list."""
        return len(self._work)

    @property
    def progress(self) -> tuple[int, int]:
        """How far the review went.

        Returns:
            The events chosen, and the files chosen one by one.
        """
        return len(self._events), len(self._files)

    def state(self) -> SortState:
        """Describe every event, for the page.

        Returns:
            The state.
        """
        source = self._source
        cards = CardMaker(source.workbook, self._events, self._files)
        workbook, decisions = self.hosts
        return SortState(
            workbook=workbook,
            decisions=decisions,
            categories=categories_used(
                source.plan, source.workbook, self._events.values()
            ),
            events=tuple(cards.event(item) for item in self._work.values()),
        )

    def event(self, event_id: str) -> EventView:
        """Describe one event and its photos.

        Args:
            event_id: The event.

        Returns:
            Its card and its photos, in date order.
        """
        item = self._item(event_id)
        cards = CardMaker(self._source.workbook, self._events, self._files)
        photos = tuple(cards.photo(row) for row in item.rows)
        return EventView(card=cards.event(item), photos=photos)

    def preview_source(self, row_id: str) -> Path | None:
        """Find the file a preview shows.

        Args:
            row_id: The row, from the page.

        Returns:
            It, in the container; None for an unknown row.
        """
        row = self._rows.get(row_id)
        return None if row is None else self._source.mapper.to_container(row.path)

    def choose_event(self, event_id: str, value: EventValue) -> EventView:
        """Name an event, give it a category, or leave it where it is; then save.

        Args:
            event_id: The event.
            value: The choice.

        Returns:
            The event, as chosen.

        Raises:
            DecisionsError: An unknown event, or nothing chosen.
        """
        self._item(event_id)
        if value.empty:
            raise DecisionsError(_("Type a name or a category, or leave it in place."))
        base = EventValue.of(self._source.workbook.events.get(event_id))
        self._events[event_id] = EventDecision(event=event_id, value=value, base=base)
        return self._saved(event_id)

    def send(self, request: SendFiles) -> EventView:
        """Send photos of an event to another category, or leave them; then save.

        Args:
            request: The photos and where they go.

        Returns:
            The event, as chosen.
        """
        rows = movable_rows(self._item(request.event), request)
        for decision in file_decisions(self._source, rows, request):
            self._files[decision.row] = decision
        return self._saved(request.event)

    def forget(self, event_id: str, rows: tuple[str, ...]) -> EventView:
        """Forget the page's choice of photos, or of the event: the workbook decides.

        Args:
            event_id: The event.
            rows: Its photos to forget; none: the event's own choice.

        Returns:
            The event, as chosen now.
        """
        members = {row.id for row in self._item(event_id).rows}
        for row_id in members.intersection(rows):
            self._files.pop(row_id, None)
        if not rows:
            self._events.pop(event_id, None)
        return self._saved(event_id)

    def decisions(self) -> PageDecisions:
        """Build the decisions file.

        Returns:
            Every choice of the page.
        """
        return PageDecisions(
            plan_id=self._source.plan.plan_id,
            events=tuple(self._events.values()),
            files=tuple(self._files.values()),
        )

    def _saved(self, event_id: str) -> EventView:
        """Save the decisions file, then describe the event.

        Args:
            event_id: The event just chosen.

        Returns:
            Its card and photos.
        """
        write_page_decisions(self._source.target, self.decisions())
        return self.event(event_id)

    def _item(self, event_id: str) -> WorkItem:
        """Find an event of the work list.

        Args:
            event_id: Its id.

        Returns:
            It.

        Raises:
            DecisionsError: There is no such event.
        """
        item = self._work.get(event_id)
        if item is None:
            raise DecisionsError(_("There is no such event."))
        return item
