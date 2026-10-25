"""The sort review's choices of photos, the destination typed, the rules remembered."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.page_values import EventValue
from media_hygiene.classify.rules_file import add_rule, read_rules
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.review.sort_destination import Destination, destination
from media_hygiene.review.sort_files import RuleBook, file_decisions, movable_rows
from media_hygiene.review.sort_rule import RuleIn, RulePreview, preview
from media_hygiene.review.sort_session import SortSession
from media_hygiene.review.sort_state import EventView

if TYPE_CHECKING:
    from media_hygiene.review.sort_files import SendFiles

_NANOSECONDS: Final = 1_000_000_000


class RuleSaved(BaseModel):
    """A rule written into `config.toml`, as read back, and the event chosen with it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    dates: str
    category: str
    modified: str  # of `config.toml`, ISO 8601, UTC: the page shows it in local time
    view: EventView


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

    def rule_preview(self, asked: RuleIn) -> RulePreview:
        """What a rule for an event would take on the plan shown; nothing is saved.

        Args:
            asked: The rule, as validated in the page's dialog.

        Returns:
            Its counts.
        """
        self._item(asked.event)
        return preview(
            self._source.plan, asked.event, (asked.rule(), self._source.book.rules)
        )

    def save_rule(self, asked: RuleIn) -> RuleSaved:
        """Write a rule into `config.toml`, read it back, and choose the event's folder.

        Args:
            asked: The rule, as validated in the page's dialog.

        Returns:
            The rule as the file holds it, and the event as chosen.

        Raises:
            ConfigError: The page was opened without `config.toml`, or the file refused
                the rule (a name taken, no list of rules).
        """
        self._item(asked.event)
        config = self._source.book.config
        if config is None:
            raise ConfigError(_("This page cannot write config.toml."))
        held = add_rule(config, asked.rule())
        book = RuleBook(config, read_rules(config))
        self._source = replace(self._source, book=book)
        value = EventValue(name=held.name, category=held.category)
        view = self.choose_event(asked.event, value)
        written = config.stat().st_mtime_ns / _NANOSECONDS
        return RuleSaved(
            name=held.name,
            dates=held.dates,
            category=held.category,
            modified=datetime.fromtimestamp(written, tz=UTC).isoformat(),
            view=view,
        )
