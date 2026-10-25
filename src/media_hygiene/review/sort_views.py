"""What the sort review page receives: the events of the work list, and their photos.

The state lists every event in the order of the workbook's Events sheet, without its
photos (tens of thousands); the photos of one event come with `GET /api/event/<id>`.
Each event and photo shows the workbook's value and the page's choice side by side.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.layout import render
from media_hygiene.classify.models import Band
from media_hygiene.classify.names import band_name
from media_hygiene.classify.page_overlay import Verdict, value_text, verdict
from media_hygiene.classify.page_values import EventValue, FileValue
from media_hygiene.classify.workbook.own_folders import owns_folder
from media_hygiene.review.sort_cards import EventCard, PhotoCard
from media_hygiene.review.sort_sides import event_side
from media_hygiene.review.sort_sure import reach, sure_value

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping

    from media_hygiene.classify.page_decisions import EventDecision, FileDecision
    from media_hygiene.classify.plan_file import PlanRow
    from media_hygiene.classify.workbook.edits import Edits
    from media_hygiene.classify.worklist import WorkItem
    from media_hygiene.review.sort_files import SortSource

_SHOWN_FOLDERS: Final = 3
_PERCENT: Final = 100
THUMB_PREFIX: Final = "/thumb/"
PREVIEW_PREFIX: Final = "/preview/"
JPEG_SUFFIX: Final = ".jpg"


@dataclass(frozen=True, slots=True)
class CardMaker:
    """Describes events and photos with the workbook's edits and the page's choices."""

    workbook: Edits
    events: Mapping[str, EventDecision]
    files: Mapping[str, FileDecision]
    moved: Collection[str] = ()  # the rows earlier `sort` runs of the plan moved
    rule_days: Mapping[str, str] = field(default_factory=dict)  # `date_range` rules
    layout: str = ""  # the plan's sure layout: where a guess goes once confirmed

    @classmethod
    def of(
        cls,
        source: SortSource,
        choices: tuple[Mapping[str, EventDecision], Mapping[str, FileDecision]],
        moved: Collection[str],
    ) -> CardMaker:
        """The cards of a review, from its plan and workbook and the page's choices.

        Args:
            source: The plan and the workbook.
            choices: The page's event and file choices.
            moved: The rows earlier runs moved.

        Returns:
            The maker.
        """
        events, files = choices
        days = source.book.days
        return cls(source.workbook, events, files, moved, days, source.plan.layout)

    def proposed(self, row: PlanRow) -> str:
        """Where a file is proposed to go: a guess stays until confirmed (0402).

        Args:
            row: Its row.

        Returns:
            Its folder, the one the sure layout gives a guess, or empty: it stays.
        """
        if row.folder is not None or row.band is not Band.UNSURE or not row.values:
            return row.folder or ""
        return render(self.layout, row.values.as_values()) or ""

    def event(self, item: WorkItem) -> EventCard:
        """Describe one event.

        Args:
            item: The event, from the work list.

        Returns:
            Its card.
        """
        event, head = item.event, item.proposal
        now = EventValue.of(self.workbook.events.get(event.id))
        chosen = self.events.get(event.id)
        effect = reach(item)
        ruled = Counter(row.rule for row in item.rows if row.rule).most_common(1)
        rule = ruled[0][0] if ruled else ""
        return EventCard(
            id=event.id,
            title=event.label or event.span,
            span=event.span,
            files=len(item.rows),
            undecided=item.undecided,
            share=round(item.cumulated * _PERCENT),
            folders=item.folders[:_SHOWN_FOLDERS],
            category=head.category,
            folder=self.proposed(head),
            prefix=_prefix(self.proposed(head), head.category),
            band=band_name(head.band),
            why=head.why,
            sure=sure_value(item) is not None,
            moves=effect.moves,
            kept=effect.kept,
            kept_folders=effect.folders,
            workbook=event_side(now),
            page=None if chosen is None else event_side(chosen.value),
            saved="" if chosen is None else chosen.saved,
            sorted=any(row.id in self.moved for row in item.rows),
            first_day=event.start[:10],
            last_day=event.end[:10],
            rule=rule,
            rule_days=self.rule_days.get(rule, ""),
            conflict=chosen is not None
            and verdict(now, chosen.value, chosen.base) is Verdict.CONFLICT,
        )

    def photo(self, row: PlanRow) -> PhotoCard:
        """Describe one file.

        Args:
            row: Its row.

        Returns:
            Its card.
        """
        now = FileValue.of(self.workbook.files.get(row.id))
        chosen = self.files.get(row.id)
        return PhotoCard(
            row=row.id,
            name=row.path[len(row.parent) + 1 :],
            folder=row.parent,
            date=(row.date or "").replace("T", " "),
            band=band_name(row.band),
            proposed=self.proposed(row),
            thumb=f"{THUMB_PREFIX}{row.id}{JPEG_SUFFIX}",
            preview=f"{PREVIEW_PREFIX}{row.id}{JPEG_SUFFIX}",
            movable=row.values is not None and row.band is not Band.STAY,
            own=owns_folder(row),
            workbook=value_text(now),
            page="" if chosen is None else value_text(chosen.value),
            conflict=chosen is not None
            and verdict(now, chosen.value, chosen.base) is Verdict.CONFLICT,
        )


def _prefix(folder: str, category: str) -> str:
    """The part of a proposed folder the layout writes before its category.

    Args:
        folder: The proposed folder (`2011/Fêtes`).
        category: Its category (`Fêtes`).

    Returns:
        `2011/`; empty when the folder does not end with the category.
    """
    if not category or not folder.endswith(category):
        return ""
    return folder.removesuffix(category)
