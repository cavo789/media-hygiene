"""The folders the user named, which an event choice never flattens (0385).

A sure file whose reason is `existing-folder` sits in a folder the user named. An event
accepted as proposed leaves it there; an event given another destination becomes its
parent: the user's folders stay below it, by the part of their path under the deepest
common parent of the event's user-named folders (one folder only: the destination
itself, never `Budva/Budva`). A file edit still wins over this, a category edit applies.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.models import Band, SortReason
from media_hygiene.classify.worklist import proposed_row

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow


def owns_folder(row: PlanRow) -> bool:
    """Tell whether a file sits in a folder the user named.

    Args:
        row: Its row.

    Returns:
        True for a sure `existing-folder` row that may move.
    """
    return (
        row.band is Band.SURE
        and row.reason is SortReason.EXISTING_FOLDER
        and row.values is not None
        and bool(row.category)
    )


@dataclass(frozen=True, slots=True)
class OwnFolders:
    """The user-named folders of one event, and the category the event proposes."""

    folders: tuple[str, ...]  # categories, `/`-separated, in the event's order
    proposal: str

    @classmethod
    def of(cls, rows: Sequence[PlanRow]) -> OwnFolders | None:
        """Read them from the rows of an event.

        Args:
            rows: The rows of one event.

        Returns:
            Them, or None when no file of the event sits in a folder the user named.
        """
        folders = tuple(dict.fromkeys(row.category for row in rows if owns_folder(row)))
        return cls(folders, proposed_row(rows).category) if folders else None

    def accepts(self, category: str) -> bool:
        """Tell whether a chosen category accepts the proposal: no new destination.

        Args:
            category: The category the event was given.

        Returns:
            True when it is the proposed one, or one of the user's folders.
        """
        wanted = category.casefold()
        return any(
            wanted == known.casefold() for known in (self.proposal, *self.folders)
        )

    def under(self, category: str, destination: str) -> str:
        """The category of a user-named folder once the event is given a destination.

        Args:
            category: The folder's category (`Montenegro/Budva`).
            destination: The event's (`Vacances au Monténégro`).

        Returns:
            The folder below the destination (`Vacances au Monténégro/Budva`).
        """
        shared = _common(self.folders)
        return "/".join((destination, *category.split("/")[shared:]))


def own_folders(plan: ClassifyPlan, events: Collection[str]) -> dict[str, OwnFolders]:
    """The user-named folders of the events given, those that have some.

    Args:
        plan: The plan.
        events: The ids of the events an edit names.

    Returns:
        Event id → its user-named folders.
    """
    grouped: defaultdict[str, list[PlanRow]] = defaultdict(list)
    for row in plan.rows:
        if row.event_id in events:
            grouped[row.event_id].append(row)
    found = {event: OwnFolders.of(rows) for event, rows in grouped.items()}
    return {event: folders for event, folders in found.items() if folders is not None}


def _common(folders: Sequence[str]) -> int:
    """How many leading parts every folder shares.

    Args:
        folders: Categories, `/`-separated.

    Returns:
        The number of parts of their deepest common parent; for one folder, all of it.
    """
    split = [folder.split("/") for folder in folders]
    shared = 0
    for parts in zip(*split, strict=False):
        if len(set(parts)) != 1:
            break
        shared += 1
    return shared
