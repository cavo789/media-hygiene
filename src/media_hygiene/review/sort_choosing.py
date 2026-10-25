"""The sort review's choices of photos, and the destination of what is being typed."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.review.sort_destination import Destination, destination
from media_hygiene.review.sort_files import file_decisions, movable_rows
from media_hygiene.review.sort_session import SortSession

if TYPE_CHECKING:
    from media_hygiene.classify.page_values import EventValue
    from media_hygiene.review.sort_files import SendFiles
    from media_hygiene.review.sort_state import EventView


class SortChoosing(SortSession):
    """The sort review: photos sent elsewhere, choices taken back, destinations."""

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

    def destination(self, event_id: str, value: EventValue) -> Destination:
        """Where an event's files go with a value typed for it; nothing is saved.

        Args:
            event_id: The event.
            value: What is typed for it; empty: its choice as it stands.

        Returns:
            Where its files go.
        """
        item = self._item(event_id)
        return destination(self._source, item, (self.decisions(), value))
