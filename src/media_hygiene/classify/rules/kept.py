"""`keep_folders` (0391): a rule's category becomes the parent of the user's folders.

The rule `Montenegro` (`2019-07-12..2019-07-19`, `Vacances et sorties/Montenegro`) takes
the whole trip; the user's `Montenegro/Budva`, `Montenegro/Cetinje` stay below it by the
part of their path under their deepest common parent, as an event given a
destination does (0385): `Vacances et sorties/Montenegro/Budva`. The photos that joined
those folders (`same_moment`, 0386) follow them; any other file takes the category.

Only the event's main folder (the one holding most of its files) and its relatives (the
folders sharing a parent with it) are kept (0394): the wedding's own folder is the
category itself, never below it; an unrelated folder (`Développement Sep`) goes to the
category flat. The files a `kind` rule takes (screenshots) are not counted.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import SortReason
from media_hygiene.classify.workbook.own_folders import OwnFolders

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.classify.rules.building import RuleFacts

# The signals of a file that sits in, or joins, a folder the user named.
_KEPT: Final = frozenset(
    {SortReason.EXISTING_FOLDER, SortReason.SAME_MOMENT, SortReason.EVENT_NEIGHBOUR}
)


@dataclass(frozen=True, slots=True)
class Kept:
    """What `keep_folders` and the date rules read besides the folder signals.

    `named`: event id → the main folder the user named in it and its relatives (0391).
    `aside`: the files a `kind` rule takes, never a date rule's (0394).
    """

    named: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    aside: frozenset[Path] = frozenset()


def named_folders(facts: RuleFacts) -> dict[str, tuple[str, ...]]:
    """The main folder the user named in each event, and its relatives.

    Args:
        facts: The folder signals, the events, the files a `kind` rule takes.

    Returns:
        Event id → their categories, in the event's order.
    """
    named: dict[str, Counter[str]] = {}
    for path, event in facts.event_of.items():
        signal = facts.folders[path]
        if (
            signal.reason is SortReason.EXISTING_FOLDER
            and signal.category
            and path not in facts.kept.aside
        ):
            named.setdefault(event.event_id, Counter())[signal.category] += 1
    return {event: _relatives(counts) for event, counts in named.items()}


def _relatives(counts: Counter[str]) -> tuple[str, ...]:
    """The folder holding most files, and those sharing a parent with it.

    Args:
        counts: The files of each folder, in the event's order.

    Returns:
        Their categories, in the event's order; the first on a tie is the main one.
    """
    ((main, _),) = counts.most_common(1)
    head = main.split("/")[0].casefold()
    return tuple(folder for folder in counts if folder.split("/")[0].casefold() == head)


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
    folders = facts.kept.named.get(event.event_id, ()) if event else ()
    if signal.reason not in _KEPT or signal.category not in folders:
        return category
    return OwnFolders(folders, "").under(signal.category, category)
