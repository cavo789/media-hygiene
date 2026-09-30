"""Turn the decisions of an edited plan into groups of moves, companions together.

A photo and its Live Photo video (`IMG_1.HEIC`, `IMG_1.MOV`), a RAW file and its JPEG
twin share a folder and a name: they go to the folder of the first of them (a photo,
then a RAW file, then a video), whatever the others' rows say. Their sidecars follow
them when they move (`actions/sort.py`).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.sort_plan import Move, MoveGroup, SortPlan
from media_hygiene.constants import MediaKind
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.classify.workbook.edits import Decision
    from media_hygiene.paths.host_paths import HostPathMapper

# Which companion leads its group: a photo, then a RAW file, then a video.
_LEAD: Final = {MediaKind.IMAGE: 0, MediaKind.RAW: 1, MediaKind.VIDEO: 2}


@dataclass(frozen=True, slots=True)
class PlanContext:
    """What turns decisions into moves: paths, folders never moved, earlier runs."""

    mapper: HostPathMapper
    protected: tuple[Path, ...] = ()  # container paths: their files never move
    moved_before: frozenset[str] = frozenset()  # row ids an earlier run moved


def sort_plan(
    plan_id: str, decisions: Iterable[Decision], context: PlanContext
) -> SortPlan:
    """Turn the decisions of an edited plan into moves.

    Args:
        plan_id: The classify plan.
        decisions: One decision per row, edits applied.
        context: Paths, protected folders, rows already moved.

    Returns:
        The groups to move, and the counts of what does not move.
    """
    groups: list[MoveGroup] = []
    counts = _Counts()
    for members in _companions(decisions, context.mapper):
        group = _group(members, context, counts)
        if group is not None:
            groups.append(group)
    return SortPlan(
        plan_id,
        tuple(groups),
        in_place=counts.in_place,
        stay=counts.stay,
        done=len(counts.earlier),
        moved_before=tuple(counts.earlier),
    )


@dataclass(slots=True)
class _Counts:
    """What does not move, counted while the groups are built."""

    in_place: int = 0
    stay: int = 0
    earlier: list[Path] = field(default_factory=list[Path])


def _group(
    members: list[tuple[Decision, Path]], context: PlanContext, counts: _Counts
) -> MoveGroup | None:
    """The moves of one group of companions: all follow the leading file.

    Args:
        members: The decisions and files of the group, the leading one first.
        context: Paths, protected folders, rows already moved.
        counts: Where what does not move is counted.

    Returns:
        The group, or None when none of its files moves.
    """
    lead, source = members[0]
    protected = any(is_within(source, kept) for kept in context.protected)
    if lead.folder is None or protected:
        counts.stay += len(members)
        return None
    root = context.mapper.to_container(lead.row.root)
    target = root.joinpath(*lead.folder.split("/"))
    moves: list[Move] = []
    for decision, path in members:
        row = decision.row
        if row.id in context.moved_before:
            counts.earlier.append(path)
        elif _same_folder(path.parent, target):
            counts.in_place += 1
        else:
            moves.append(Move(row.id, path, row.size, row.mtime_ns, lead.band))
    return MoveGroup(root, target, tuple(moves)) if moves else None


def _companions(
    decisions: Iterable[Decision], mapper: HostPathMapper
) -> list[list[tuple[Decision, Path]]]:
    """Group the files sharing a folder and a name, the leading one first.

    Args:
        decisions: The decisions.
        mapper: Host ↔ container paths.

    Returns:
        The groups, in the plan's order; most hold one file.
    """
    groups: defaultdict[tuple[str, str], list[tuple[Decision, Path]]]
    groups = defaultdict(list)
    for decision in decisions:
        path = mapper.to_container(decision.row.path)
        key = (str(path.parent).casefold(), PurePath(path.name).stem.casefold())
        groups[key].append((decision, path))
    return [sorted(members, key=_lead_order) for members in groups.values()]


def _lead_order(member: tuple[Decision, Path]) -> tuple[int, str]:
    """Order companions: a photo, then a RAW file, then a video; then by name.

    Args:
        member: A decision and its file.

    Returns:
        The sort key.
    """
    path = member[1]
    return (_LEAD.get(media_kind(path) or MediaKind.OTHER, len(_LEAD)), path.name)


def _same_folder(folder: Path, other: Path) -> bool:
    """Tell whether two folders are one, ignoring case (as Windows does).

    Args:
        folder: A folder.
        other: Another folder.

    Returns:
        True when they are the same.
    """
    return is_within(folder, other) and is_within(other, folder)
