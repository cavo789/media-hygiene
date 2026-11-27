"""The *🗂 Events* view of the search (0437): its parts, none reading a classify plan.

The events made from the index (0572), those found in the folders (0557), the late
photos (0558), other grouping values tried (0643) and *Try on one month* (0640). The
plan's events and their photos (`/api/events`, `/api/events/<id>`) left in 0822.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.found_desk import FoundDesk
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.grouping_desk import GroupingPreview
    from media_hygiene.search.late_desk import LateDesk
    from media_hygiene.search.span_events import SpanEvents
    from media_hygiene.services.sort_trial_page import SortTrial

EVENTS_PAGE_PATH: Final = "/events"


@dataclass(frozen=True, slots=True)
class EventsDesk:  # pylint: disable=too-many-instance-attributes  # one per view
    """Answers the Events view: one field per part, None when the page has none."""

    index: SearchIndex
    mapper: HostPathMapper
    chosen: Callable[[], frozenset[str]]  # the host paths set aside
    found: FoundDesk | None = None  # *Events found in your folders* (0557)
    late: LateDesk | None = None  # *New photos during an event* (0558)
    span: SpanEvents | None = None  # the events made from the index (0572)
    grouping: GroupingPreview | None = None  # other grouping values tried (0643)
    trial: SortTrial | None = None  # *Try on one month* (0640)
