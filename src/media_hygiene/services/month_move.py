"""*Move to their month* on the library page (0623): sorted without an event.

Each photo picked goes to its own `YYYY/YYYY-MM`, below the target chosen or its root
(an event takes the earliest photo's month for all). The date is the one a move to an
event reads (`EventPlace.dated`). A file without a date stays, never guessed; a file in
its month stays too, whether the plan knows it or not: a file in an event of that month
is not in the month itself, and moves. The rest is the journaled sort of a group.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.i18n import ngettext
from media_hygiene.services.event_place import EventPlace, month_folder
from media_hygiene.services.group_match import sits_in
from media_hygiene.services.group_sort import moved_group
from media_hygiene.services.group_sort_models import GroupMove
from media_hygiene.services.selection_models import MonthGroup, MonthView, Picked

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.selection_move import SelectionMover


@dataclass(frozen=True, slots=True)
class _Sorted:
    """The files picked, sorted out: by month to move, already there, without a date."""

    place: EventPlace
    months: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))
    there: list[int] = field(default_factory=list)
    undated: list[int] = field(default_factory=list)

    def folders(self) -> dict[Path, str]:
        """The files to move and their month.

        Returns:
            Container path → its folder below its root.
        """
        paths = self.place.chosen.paths
        return {
            paths[key]: month for month, keys in self.months.items() for key in keys
        }


def _sorted_out(mover: SelectionMover, chosen: Picked) -> _Sorted:
    """Sort the files picked out, with the settings the disk holds now.

    Args:
        mover: The page's mover: the plan's rows.
        chosen: The files picked and their dates.

    Returns:
        Them.
    """
    place = EventPlace(mover.runtime.with_overrides({}), mover.rows(), chosen)
    found = _Sorted(place)
    mapper = place.runtime.mapper
    target = place.root()
    root = mapper.to_host(target) if target else None
    for key, path in sorted(chosen.paths.items()):
        when = place.dated(path)
        if when is None:
            found.undated.append(key)
        elif sits_in(mapper.to_host(path), month_folder(when), root):
            found.there.append(key)
        else:
            found.months[month_folder(when)].append(key)
    return found


def month_view(mover: SelectionMover, chosen: Picked) -> MonthView:
    """What the move would do, before it runs.

    Args:
        mover: The page's mover.
        chosen: The files picked and their dates.

    Returns:
        The months, as the user will see them, and the files that stay.
    """
    found = _sorted_out(mover, chosen)
    place = found.place
    months = tuple(
        MonthGroup(
            target=EventPlace(
                place.runtime,
                place.rows,
                Picked({key: chosen.paths[key] for key in keys}),
            ).below(month),
            keys=tuple(keys),
        )
        for month, keys in sorted(found.months.items())
    )
    return MonthView(
        months=months,
        there=tuple(found.there),
        undated=tuple(found.undated),
        moves=sum(len(group.keys) for group in months),
    )


def move_to_months(mover: SelectionMover, chosen: Picked) -> dict[str, object]:
    """Move each file to its month, journaled, read back.

    Args:
        mover: The page's mover.
        chosen: The files picked and their dates.

    Returns:
        The run, as the disk holds it, and what stayed, said in `kept`.
    """
    found = _sorted_out(mover, chosen)
    move = GroupMove(found.folders(), "", found.place.root())
    answer = moved_group(found.place.runtime, move)
    answer["undated"] = len(found.undated)
    answer["there"] = len(found.there)
    answer["kept"] = _kept_said(len(found.there), len(found.undated))
    return answer


def _kept_said(there: int, undated: int) -> str:
    """Say which files stayed, and why.

    Args:
        there: The files already in their month.
        undated: The files without a date.

    Returns:
        The sentences; empty when every file moved.
    """
    said = []
    if there:
        said.append(
            ngettext(
                "{n} file is already in its month: not moved.",
                "{n} files are already in their month: not moved.",
                there,
            ).format(n=there)
        )
    if undated:
        said.append(
            ngettext(
                "{n} file has no date: left where it is.",
                "{n} files have no date: left where they are.",
                undated,
            ).format(n=undated)
        )
    return " ".join(said)
