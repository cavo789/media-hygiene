"""Where an event's files go with the folder being typed, computed as `sort` will.

The page asks while the user types (`POST /api/destination`): the workbook's edits, the
page's choices and the value typed for this event are laid over the plan's rows of the
event, then `resolve` decides each file, the folders the user named included (0385).
Nothing is saved.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.page_overlay import overlay
from media_hygiene.classify.workbook.edits import resolve
from media_hygiene.classify.workbook.own_folders import owns_folder

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.classify.page_decisions import PageDecisions
    from media_hygiene.classify.page_values import EventValue
    from media_hygiene.classify.workbook.edits import Decision
    from media_hygiene.classify.worklist import WorkItem
    from media_hygiene.review.sort_files import SortSource

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class Destination(BaseModel):
    """What the folder typed for an event does to its files."""

    model_config = _FROZEN

    target: str  # the host folder most of its files go to; empty: they stay
    going: int  # files that go there
    already: int  # of which already sit there
    kept: int  # files that keep a folder the user named, elsewhere
    kept_folders: tuple[str, ...]  # those folders, their last part
    stay: int  # files left where they are
    elsewhere: int  # files sent to another folder, one by one


def destination(
    source: SortSource, item: WorkItem, chosen: tuple[PageDecisions, EventValue]
) -> Destination:
    """Resolve the files of one event with a value typed for it.

    Args:
        source: The plan and the workbook's edits.
        item: The event.
        chosen: The page's choices, and the value typed for this event (empty: none).

    Returns:
        Where its files go.
    """
    page, value = chosen
    edits = overlay(source.workbook, page).edits
    events = dict(edits.events)
    if not value.empty:
        events[item.event.id] = value.edit()
    plan = source.plan.model_copy(update={"rows": item.rows})
    decisions = resolve(plan, replace(edits, events=events))
    placed = Counter(
        (d.row.root, d.folder)
        for d in decisions
        if d.folder is not None and not owns_folder(d.row)
    )
    return _tally(decisions, placed.most_common(1)[0][0] if placed else None)


def _tally(decisions: Sequence[Decision], main: tuple[str, str] | None) -> Destination:
    """Count where the files of an event go.

    Args:
        decisions: One per file of the event.
        main: The root and the folder most of them go to; None: none moves.

    Returns:
        The destination.
    """
    going = [
        d
        for d in decisions
        if main is not None and d.folder is not None and (d.row.root, d.folder) == main
    ]
    kept = [
        d
        for d in decisions
        if d.folder is not None and owns_folder(d.row) and d not in going
    ]
    stay = sum(1 for d in decisions if d.folder is None)
    return Destination(
        target="" if main is None else host_folder(*main),
        going=len(going),
        already=sum(
            1 for d in going if d.row.model_copy(update={"folder": d.folder}).in_place
        ),
        kept=len(kept),
        kept_folders=tuple(
            dict.fromkeys((d.folder or "").rsplit("/", 1)[-1] for d in kept)
        ),
        stay=stay,
        elsewhere=len(decisions) - len(going) - len(kept) - stay,
    )


def host_folder(root: str, folder: str) -> str:
    r"""A folder below a host root, written as the host writes it.

    Args:
        root: `C:\Photos`, or `/home/me/Photos`.
        folder: `2011/Fêtes`, `/`-separated.

    Returns:
        `C:\Photos\2011\Fêtes`.
    """
    separator = "\\" if "\\" in root or root[1:2] == ":" else "/"
    return separator.join((root.rstrip("\\/"), *folder.split("/")))
