"""The lines of `mh push`'s plan piped back to the container (0264).

`mh` pipes the plan back to the run that journals it before Windows acts, and to the
run that proves it after: the changes (moves, set-asides) and the copies, each path
turned back into a path relative to the target.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.plan.push_entries import Entry, Stat
from media_hygiene.services.push_lines import Change, Order

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.services.push_place import Target

_TAB: Final = "\t"
_ENTRY_FIELDS: Final = 3  # path, size, mtime_ns


@dataclass(frozen=True, slots=True)
class ReadPlan:
    """The lines piped back: the run, its changes, what robocopy was to copy."""

    run_id: str = ""
    changes: tuple[Change, ...] = ()
    copies: tuple[Entry, ...] = ()


def read_plan(lines: Iterable[str], target: Target) -> ReadPlan:
    """Read the lines piped back.

    Args:
        lines: The plan's lines, as `plan_lines` wrote them.
        target: The target, to turn its host paths into relative ones.

    Returns:
        The run, its changes and its copies; a line not understood is skipped.
    """
    run_id = ""
    changes: list[Change] = []
    copies: list[Entry] = []
    for line in lines:
        fields = line.rstrip("\r\n").split(_TAB)
        kind = fields[0]
        if kind == Order.RUN and len(fields) > 1:
            run_id = fields[1]
        elif kind in {Order.MOVE, Order.ASIDE, Order.REMOVE}:
            change = _read_change(Order(kind), fields[1:], target)
            if change is not None:
                changes.append(change)
        elif kind == Order.COPY:
            entry = _read_entry(fields[1:], target)
            if entry is not None:
                copies.append(entry)
    return ReadPlan(run_id, tuple(changes), tuple(copies))


def _read_change(order: Order, fields: list[str], target: Target) -> Change | None:
    """Read one change.

    Args:
        order: Its kind.
        fields: `old`, `new`, `size`, `mtime_ns`, maybe a reason.
        target: The target.

    Returns:
        It; None when a field is missing or outside the target.
    """
    entry = _read_entry([fields[0], *fields[2:]], target) if len(fields) > 1 else None
    new = target.relative(fields[1]) if len(fields) > 1 else None
    if entry is None or new is None:
        return None
    return Change(order, entry, new)


def _read_entry(fields: list[str], target: Target) -> Entry | None:
    """Read a path of the target with its size and time.

    Args:
        fields: `path`, `size`, `mtime_ns`.
        target: The target.

    Returns:
        It; None when a field is missing, not a number, or outside the target.
    """
    if len(fields) < _ENTRY_FIELDS or not fields[1].isdigit():
        return None
    if not fields[2].lstrip("-").isdigit():
        return None
    relative = target.relative(fields[0])
    if relative is None:
        return None
    return Entry(relative, Stat(int(fields[1]), int(fields[2])))
