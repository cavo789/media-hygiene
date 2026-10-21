r"""The plan of `mh backup` as lines, between the container and Windows (0264).

One line per order, its kind first, fields separated by a tab, host paths as Windows
writes them; `mh` applies them in this order and pipes them back for the journal and
the proof:

- `run <id>`, `threads <n>`, then `stop` when the safety stop holds the run;
- `source <photo folder> <its folder in the target>`: one robocopy each;
- `exclude <name or folder>` (robocopy `/XD`), `broken <file>` (`/XF`: never
  replaces its copy);
- `expired <folder of .removed>`: erased;
- `move <old> <new> <size> <mtime_ns>`: a rename on the target;
- `aside` and `remove <old> <in .removed> <size> <mtime_ns> [reason]`: set aside;
- `copy <path in the target> <size> <mtime_ns>`: what robocopy is to copy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.services.backup_place import REMOVED_FOLDER, host_join

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.plan.backup_entries import Entry, Stat
    from media_hygiene.services.backup_place import Target
    from media_hygiene.services.backup_run import Prepared

_TAB: Final = "\t"
# The hidden command running the container's steps, for `mh` only.
BACKUP_STEP: Final = "backup-step"


class BackupStep(StrEnum):
    """A step of `mh backup` run by the container."""

    PLAN = "plan"
    START = "start"
    PROVE = "prove"
    UNDO = "undo"
    UNDONE = "undone"


class Order(StrEnum):
    """The kind of a line."""

    RUN = "run"
    THREADS = "threads"
    STOP = "stop"
    SOURCE = "source"
    EXCLUDE = "exclude"
    BROKEN = "broken"
    EXPIRED = "expired"
    MOVE = "move"
    ASIDE = "aside"
    REMOVE = "remove"
    COPY = "copy"


@dataclass(frozen=True, slots=True)
class Change:
    """A file renamed on the target: moved, or set aside in `.removed`."""

    order: Order
    old: Entry  # its path relative to the target, before
    new: str  # its path relative to the target, after
    reason: str = ""  # why a file is removed (`GoneReason`)


def plan_lines(prepared: Prepared) -> Iterator[str]:
    """Write the plan as lines.

    Args:
        prepared: The plan of the run.

    Yields:
        Each line, without its end.
    """
    yield from _setup_lines(prepared)
    target = prepared.target
    for change in plan_changes(prepared):
        line = _line(change.order, *_hosts(target, change), *_stat(change.old.stat))
        yield f"{line}{_TAB}{change.reason}" if change.reason else line
    for entry in prepared.plan.copies:
        yield _line(Order.COPY, target.host_of(entry.path), *_stat(entry.stat))


def plan_changes(prepared: Prepared) -> Iterator[Change]:
    """The renames on the target: the moves, then what is set aside in `.removed`.

    Args:
        prepared: The plan of the run.

    Yields:
        Each change.
    """
    plan = prepared.plan
    removed = f"{REMOVED_FOLDER}/{prepared.run_id}"
    for move in plan.moves:
        yield Change(Order.MOVE, move.old, move.new)
    for edit in plan.edited:
        yield Change(Order.ASIDE, edit.old, f"{removed}/{edit.old.path}")
    for gone in plan.removals:
        aside = f"{removed}/{gone.entry.path}"
        yield Change(Order.REMOVE, gone.entry, aside, gone.reason.value)


def _setup_lines(prepared: Prepared) -> Iterator[str]:
    """The lines before the changes: the run, the folders, what robocopy skips.

    Args:
        prepared: The plan of the run.

    Yields:
        Each line.
    """
    target = prepared.target
    yield _line(Order.RUN, prepared.run_id)
    yield _line(Order.THREADS, str(prepared.threads))
    if prepared.stopped:
        yield _line(Order.STOP)
    for source in prepared.sources:
        yield _line(Order.SOURCE, source.host, target.host_of(source.prefix))
    for name in prepared.excluded:
        yield _line(Order.EXCLUDE, name)
    for entry in prepared.plan.broken:
        yield _line(Order.BROKEN, _pc_host(prepared, entry.path))
    for folder in prepared.expired:
        yield _line(Order.EXPIRED, target.host_of(folder))


def _hosts(target: Target, change: Change) -> tuple[str, str]:
    """Where Windows finds a changed file, before and after.

    Args:
        target: The target.
        change: The change.

    Returns:
        Both host paths.
    """
    return target.host_of(change.old.path), target.host_of(change.new)


def _pc_host(prepared: Prepared, relative: str) -> str:
    """Where a path of the target lies on the PC, as Windows writes it.

    Args:
        prepared: The plan, with its sources.
        relative: A path relative to the target, below a source's folder.

    Returns:
        The host path of the PC file.
    """
    for source in prepared.sources:
        head = f"{source.prefix}/"
        if relative.casefold().startswith(head.casefold()):
            return host_join(source.host, relative[len(head) :])
    return relative


def _stat(stat: Stat) -> tuple[str, str]:
    """A size and a time as fields.

    Args:
        stat: Them.

    Returns:
        Both, in decimal.
    """
    return str(stat.size), str(stat.mtime_ns)


def _line(order: Order, *fields: str) -> str:
    """One line.

    Args:
        order: Its kind.
        *fields: Its fields.

    Returns:
        The kind and the fields, separated by tabs.
    """
    return _TAB.join((order.value, *fields))
