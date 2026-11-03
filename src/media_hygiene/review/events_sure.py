"""The sure proposals of the sort review: the events one click may accept.

An event's proposal is sure when the folder most of its files get comes from the sure
band, with a category, while some of its files are still to check or to sort and none
of those proposes another category. Accepting it records what Enter records on an
untouched event: that category, no name; its files then follow it, as they would
after Enter, but those in a folder the user named, which keep it (0385; `reach` counts
both for the page). Nothing is imposed: the page only offers it, the user accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.models import Band
from media_hygiene.classify.page_values import EventValue
from media_hygiene.classify.workbook.own_folders import OwnFolders, owns_folder
from media_hygiene.classify.worklist import WORK_BANDS

if TYPE_CHECKING:
    from media_hygiene.classify.worklist import WorkItem


def sure_value(item: WorkItem) -> EventValue | None:
    """The choice accepting an event's proposal records, when that proposal is sure.

    Args:
        item: The event, from the work list.

    Returns:
        Its proposed category, as an event choice; None when the proposal is not
        sure, or when nothing of the event is left to decide.
    """
    head = item.proposal
    if head.band is not Band.SURE or not head.category or not item.undecided:
        return None
    others = {row.category for row in item.rows if row.band in WORK_BANDS}
    if others - {"", head.category}:
        return None
    return EventValue(category=head.category)


@dataclass(frozen=True, slots=True)
class Reach:
    """What accepting an event's proposal does to its files."""

    moves: int  # files that leave the folder they are in
    kept: int  # files that keep a folder the user named, other than the proposed one
    folders: tuple[str, ...]  # those folders, their last part


def reach(item: WorkItem) -> Reach:
    """Count the files accepting an event's proposal moves, and those it leaves.

    Args:
        item: The event, from the work list.

    Returns:
        The files that move, and those that keep the folder the user named.
    """
    head = item.proposal
    owned = OwnFolders.of(item.rows)
    moves, kept, folders = 0, 0, dict[str, None]()
    for row in item.rows:
        if row.values is None or row.band is Band.STAY:
            continue
        if (
            owned is not None
            and owns_folder(row)
            and not _same(row.category, head.category)
        ):
            kept += 1
            folders[row.category.rsplit("/", 1)[-1]] = None
        elif not row.model_copy(update={"folder": head.folder}).in_place:
            moves += 1
    return Reach(moves, kept, tuple(folders))


def _same(category: str, other: str) -> bool:
    """Tell whether two categories name the same folder, case ignored.

    Args:
        category: One.
        other: The other.

    Returns:
        True when they do.
    """
    return category.casefold() == other.casefold()
