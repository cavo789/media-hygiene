"""The two steps of *Move to an event…* (0403): where the photos would go, the move.

`viewed` answers the move view with its one-sentence destination (0574, the Events
card) and, only when *Also remember it as an event* is ticked, the event foreseen;
`moved_now` moves the files ticked and remembers the event only when the box is ticked
(0573: a plain filing writes nothing besides the files).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.search.event_match import Moved
from media_hygiene.search.move_event import (
    cameras_of,
    foreseen,
    goes_said,
    remember_event,
)
from media_hygiene.services.selection_models import event_path

if TYPE_CHECKING:
    from media_hygiene.search.move_go import MoveIn
    from media_hygiene.search.rule_desk import RuleDesk
    from media_hygiene.services.selection_models import Picked
    from media_hygiene.services.selection_move import SelectionMover


async def viewed(desk: RuleDesk, asked: MoveIn, chosen: Picked) -> dict[str, object]:
    """Where the files picked would go, and what the move would remember.

    Args:
        desk: The rule's desk, its mover set.
        asked: The keys and the name.
        chosen: The files picked.

    Returns:
        The view, its sentence (0574) and the event foreseen (box ticked, 0573).
    """
    view = await asyncio.to_thread(mover_of(desk).view, chosen, asked.name)
    answer: dict[str, object] = view.model_dump()
    answer["goes"] = goes_said(view)  # the Events card's sentence (0574)
    answer["remembers"] = ""
    if asked.remember:
        moved = moved_of(desk, view.name, chosen)
        config = mover_of(desk).runtime.locations.config_file
        answer["remembers"] = foreseen(config, moved)
    return answer


async def moved_now(desk: RuleDesk, asked: MoveIn, chosen: Picked) -> dict[str, object]:
    """Move the files ticked; remember the event only when the box is ticked (0573).

    Args:
        desk: The rule's desk, its mover set.
        asked: The keys, the name, the box.
        chosen: The files ticked.

    Returns:
        The run read back, and the event remembered (or nothing).
    """
    answer = await asyncio.to_thread(mover_of(desk).move, chosen, asked.name)
    desk.index.built = None  # this page moved files: its next search reads them
    answer["remembered"] = ""
    if asked.remember:
        moved = moved_of(desk, event_path(asked.name), chosen)
        config = mover_of(desk).runtime.locations.config_file
        answer["remembered"] = remember_event(config, moved)
    return answer


def moved_of(desk: RuleDesk, name: str, chosen: Picked) -> Moved:
    """What a move brings to its event: the name, the days, the cameras.

    Args:
        desk: The rule's desk: the index.
        name: The event's folder name.
        chosen: The files picked and their dates.

    Returns:
        The move.
    """
    days = tuple(sorted(when.date() for when in chosen.days.values()))
    devices = cameras_of(desk.index.connection, tuple(chosen.paths))
    return Moved(name, days, devices)


def mover_of(desk: RuleDesk) -> SelectionMover:
    """The page's mover: checked before any move.

    Args:
        desk: The rule's desk.

    Returns:
        Its mover.

    Raises:
        MediaHygieneError: The page cannot move files.
    """
    if desk.mover is None:  # pragma: no cover - checked before any move
        raise MediaHygieneError(
            _("This page cannot move files: run 'sort' in the terminal.")
        )
    return desk.mover
