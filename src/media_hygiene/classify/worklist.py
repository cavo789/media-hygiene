"""The events as a work list: naming the first ones covers most of the collection.

Undecided events first (files to check or to sort), largest first, with the cumulated
share of the files left; decided events last. The Events sheet and the report share
this order, so the user goes back and forth between the two windows.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import Band

if TYPE_CHECKING:
    from media_hygiene.classify.plan_file import ClassifyPlan, PlanEvent, PlanRow

WORK_BANDS: Final = frozenset({Band.UNSURE, Band.MANUAL})


@dataclass(frozen=True, slots=True)
class WorkItem:
    """One event, its files, and how much of the work it holds."""

    event: PlanEvent
    rows: tuple[PlanRow, ...]  # in date order
    undecided: int  # files to check or to sort
    cumulated: float  # share of every file left, this event and the ones above

    @property
    def folders(self) -> tuple[str, ...]:
        """The host folders the event's files come from, the fullest first.

        Returns:
            Them.
        """
        parents = Counter(row.parent for row in self.rows)
        return tuple(folder for folder, _count in parents.most_common())

    @property
    def proposal(self) -> PlanRow:
        """The row whose folder most of the event's files get.

        Returns:
            That row.
        """
        folders = Counter(row.folder for row in self.rows)
        common = folders.most_common(1)[0][0]
        return next(row for row in self.rows if row.folder == common)


def work_list(plan: ClassifyPlan) -> tuple[WorkItem, ...]:
    """Order the events of a plan by the work they save.

    Args:
        plan: The plan.

    Returns:
        The events, undecided and largest first, with their cumulated share.
    """
    rows = {row.id: row for row in plan.rows}
    left = sum(1 for row in plan.rows if row.band in WORK_BANDS)
    grouped = [
        (event, tuple(rows[row_id] for row_id in event.rows if row_id in rows))
        for event in plan.events
    ]
    counted = [
        (event, members, sum(1 for row in members if row.band in WORK_BANDS))
        for event, members in grouped
        if members
    ]
    counted.sort(key=lambda item: (item[2] == 0, -len(item[1]), item[0].start))
    items: list[WorkItem] = []
    done = 0
    for event, members, undecided in counted:
        done += undecided
        items.append(WorkItem(event, members, undecided, done / left if left else 1.0))
    return tuple(items)
