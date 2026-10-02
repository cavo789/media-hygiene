"""What the sort review page receives: the events of the work list, and their photos.

The state lists every event in the order of the workbook's Events sheet, without its
photos (tens of thousands); the photos of one event come with `GET /api/event/<id>`.
Each event and photo shows the workbook's value and the page's choice side by side.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.models import Band
from media_hygiene.classify.names import band_name
from media_hygiene.classify.page_overlay import Verdict, value_text, verdict
from media_hygiene.classify.page_values import EventValue, FileValue

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.classify.page_decisions import EventDecision, FileDecision
    from media_hygiene.classify.plan_file import PlanRow
    from media_hygiene.classify.workbook.edits import Edits
    from media_hygiene.classify.worklist import WorkItem

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_SHOWN_FOLDERS: Final = 3
_PERCENT: Final = 100
THUMB_PREFIX: Final = "/thumb/"
PREVIEW_PREFIX: Final = "/preview/"
JPEG_SUFFIX: Final = ".jpg"


class Side(BaseModel):
    """A value as the page shows it: its text, and its parts to fill the fields."""

    model_config = _FROZEN

    text: str = ""
    name: str = ""
    category: str = ""
    stay: bool = False


class EventCard(BaseModel):
    """One event of the work list, without its photos."""

    model_config = _FROZEN

    id: str
    title: str  # its label, else its dates
    span: str
    files: int
    undecided: int  # files to check or to sort
    share: int  # cumulated share of the work, in percent
    folders: tuple[str, ...]  # where its files come from, the fullest first
    category: str  # proposed
    folder: str  # proposed, relative to the target; empty: stays
    band: str
    why: str
    workbook: Side
    page: Side | None
    conflict: bool


class PhotoCard(BaseModel):
    """One file of an event."""

    model_config = _FROZEN

    row: str
    name: str
    folder: str  # where it is, on the host
    date: str
    band: str
    proposed: str  # its proposed folder; empty: stays
    thumb: str
    preview: str
    movable: bool  # files left as they are ignore every choice
    workbook: str
    page: str
    conflict: bool


def event_side(value: EventValue) -> Side:
    """Show an event's value.

    Args:
        value: The workbook's or the page's.

    Returns:
        Its text and parts.
    """
    return Side(
        text=value_text(value),
        name=value.name,
        category=value.category,
        stay=value.stay,
    )


@dataclass(frozen=True, slots=True)
class CardMaker:
    """Describes events and photos with the workbook's edits and the page's choices."""

    workbook: Edits
    events: Mapping[str, EventDecision]
    files: Mapping[str, FileDecision]

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
        return EventCard(
            id=event.id,
            title=event.label or event.span,
            span=event.span,
            files=len(item.rows),
            undecided=item.undecided,
            share=round(item.cumulated * _PERCENT),
            folders=item.folders[:_SHOWN_FOLDERS],
            category=head.category,
            folder=head.folder or "",
            band=band_name(head.band),
            why=head.why,
            workbook=event_side(now),
            page=None if chosen is None else event_side(chosen.value),
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
            proposed=row.folder or "",
            thumb=f"{THUMB_PREFIX}{row.id}{JPEG_SUFFIX}",
            preview=f"{PREVIEW_PREFIX}{row.id}{JPEG_SUFFIX}",
            movable=row.values is not None and row.band is not Band.STAY,
            workbook=value_text(now),
            page="" if chosen is None else value_text(chosen.value),
            conflict=chosen is not None
            and verdict(now, chosen.value, chosen.base) is Verdict.CONFLICT,
        )
