"""`keep_folders` (0391): a rule's category becomes the parent of the user's folders.

The rule `Montenegro` (`2019-07-12..2019-07-19`, `Vacances et sorties/Montenegro`) takes
the whole trip; the user's `Montenegro/Budva`, `Montenegro/Cetinje` stay below it by the
part of their path under their deepest common parent, as an event given a
destination does (0385): `Vacances et sorties/Montenegro/Budva`. The photos that joined
those folders (`same_moment`, 0386) follow them; any other file takes the category.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import SortReason
from media_hygiene.classify.workbook.own_folders import OwnFolders

if TYPE_CHECKING:
    from media_hygiene.classify.models import MediaInput
    from media_hygiene.classify.rules.building import RuleFacts

# The signals of a file that sits in, or joins, a folder the user named.
_KEPT: Final = frozenset(
    {SortReason.EXISTING_FOLDER, SortReason.SAME_MOMENT, SortReason.EVENT_NEIGHBOUR}
)


def named_folders(facts: RuleFacts) -> dict[str, tuple[str, ...]]:
    """The folders the user named in each event, in the event's order.

    Args:
        facts: The folder signals and the events.

    Returns:
        Event id → their categories.
    """
    named: dict[str, dict[str, None]] = {}
    for path, event in facts.event_of.items():
        signal = facts.folders[path]
        if signal.reason is SortReason.EXISTING_FOLDER and signal.category:
            named.setdefault(event.event_id, {})[signal.category] = None
    return {event: tuple(folders) for event, folders in named.items()}


def kept_below(category: str, file: MediaInput, facts: RuleFacts) -> str:
    """The category of a `keep_folders` rule for one file: its own folder kept below.

    Args:
        category: The rule's category (`Vacances et sorties/Montenegro`).
        file: The file.
        facts: Its folder signal (joined to a user's folder: `same_moment`), its event.

    Returns:
        `…/Montenegro/Budva` for a file of (or joined to) `Montenegro/Budva`; the
        category itself for any other file, or when the event has one named folder.
    """
    signal = facts.folders[file.path]
    event = facts.event_of.get(file.path)
    folders = facts.named.get(event.event_id, ()) if event else ()
    if signal.reason not in _KEPT or signal.category not in folders:
        return category
    return OwnFolders(folders, "").under(signal.category, category)
