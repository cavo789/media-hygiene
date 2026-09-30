"""What the classify report shows: the work list by year, and the proposed tree.

Events keep the ids and the order of the workbook's Events sheet, so the user goes back
and forth between the two windows. Each event shows up to 8 thumbnails spread over its
span. Files outside any event are grouped by proposed folder.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import Band
from media_hygiene.classify.names import band_name
from media_hygiene.classify.worklist import WORK_BANDS, work_list

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow

THUMBNAILS_PER_GROUP: Final = 8


@dataclass(frozen=True, slots=True)
class GroupView:
    """An event, or the loose files of one proposed folder."""

    key: str  # the event id, or the proposed folder
    title: str
    rows: tuple[PlanRow, ...]
    undecided: int
    cumulated: float | None  # the Events sheet's cumulated share; None: no event
    head: PlanRow  # the row whose proposal most of the group's files share

    @property
    def proposal(self) -> str | None:
        """The proposed folder.

        Returns:
            It; None: the files stay where they are.
        """
        return self.head.folder

    @property
    def band(self) -> str:
        """The band of the proposal, translated.

        Returns:
            Its name.
        """
        return band_name(self.head.band)

    @property
    def reason(self) -> str:
        """Why the files go there.

        Returns:
            The reason.
        """
        return self.head.reason.value

    @property
    def shown(self) -> tuple[PlanRow, ...]:
        """Up to 8 files, spread over the group's span.

        Returns:
            Them, in date order.
        """
        return spread(self.rows, THUMBNAILS_PER_GROUP)

    @property
    def folders(self) -> tuple[str, ...]:
        """The host folders the files come from, the fullest first.

        Returns:
            Them.
        """
        return tuple(
            name for name, _n in Counter(r.parent for r in self.rows).most_common()
        )


def spread(rows: Sequence[PlanRow], count: int) -> tuple[PlanRow, ...]:
    """Pick `count` rows evenly, the first and the last included.

    Args:
        rows: Rows in date order.
        count: How many.

    Returns:
        The picked rows.
    """
    if len(rows) <= count:
        return tuple(rows)
    step = (len(rows) - 1) / (count - 1)
    return tuple(rows[round(index * step)] for index in range(count))


def year_groups(plan: ClassifyPlan) -> dict[int, list[GroupView]]:
    """The groups of each year: events in work-list order, then loose files.

    Args:
        plan: The plan.

    Returns:
        Year → its groups; 0 for the files without a year.
    """
    years: dict[int, list[GroupView]] = defaultdict(list)
    in_events: set[str] = set()
    for item in work_list(plan):
        head = item.proposal
        in_events.update(row.id for row in item.rows)
        years[_year(head)].append(
            GroupView(
                key=item.event.id,
                title=item.event.label or item.event.span,
                rows=item.rows,
                undecided=item.undecided,
                cumulated=item.cumulated if item.undecided else None,
                head=head,
            )
        )
    loose: dict[tuple[int, str | None], list[PlanRow]] = defaultdict(list)
    for row in plan.rows:
        if row.id not in in_events:
            loose[_year(row), row.folder].append(row)
    for (year, folder), rows in sorted(loose.items(), key=lambda i: -len(i[1])):
        rows.sort(key=lambda row: row.date or "")
        years[year].append(_loose(folder, tuple(rows)))
    return dict(sorted(years.items()))


def work_left(plan: ClassifyPlan) -> int:
    """The files to check or to sort.

    Args:
        plan: The plan.

    Returns:
        Their count.
    """
    return sum(1 for row in plan.rows if row.band in WORK_BANDS)


def _loose(folder: str | None, rows: tuple[PlanRow, ...]) -> GroupView:
    """The files outside any event that go to one folder.

    Args:
        folder: Their proposed folder.
        rows: Them, in date order.

    Returns:
        Their group.
    """
    return GroupView(
        key=folder or "",
        title=folder or "",
        rows=rows,
        undecided=sum(1 for row in rows if row.band in WORK_BANDS),
        cumulated=None,
        head=rows[0],
    )


def _year(row: PlanRow) -> int:
    """The year folder of a row.

    Args:
        row: A row.

    Returns:
        Its year; 0 when undated (only its date on the disk is known).
    """
    if row.values is None or row.band is Band.UNDATED:
        return 0
    return row.values.year
