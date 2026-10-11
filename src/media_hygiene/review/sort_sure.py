"""The sure proposals of the sort review: the events one click may accept.

An event's proposal is sure when the folder most of its files get comes from the sure
band, with a category, while some of its files are still to check or to sort and none
of those proposes another category. Accepting it records what Enter records on an
untouched event: that category, no name; its files then follow it, as they would
after Enter. Nothing is imposed: the page only offers it, the user accepts it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.models import Band
from media_hygiene.classify.page_values import EventValue
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
