"""The closing run of `mh push`: what the target holds now, read back (0264).

After Windows renamed and robocopy copied, the photo folders and the target are listed
again: each copy the plan asked for found with its size and date (a copy robocopy
failed named), each rename seen made and journaled `done`, every file of the PC found
in the target (a broken one apart), the bytes copied journaled per photo folder.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.plan.push_entries import Entry
from media_hygiene.services.push_broken import BrokenFinder, ContentCheck
from media_hygiene.services.push_journal import push_run, record_done
from media_hygiene.services.push_read import read_plan
from media_hygiene.services.push_run import list_sides, push_filters
from media_hygiene.services.push_sources import push_target

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.plan.push_entries import Stat
    from media_hygiene.services.push_read import ReadPlan
    from media_hygiene.services.push_run import Sides
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class ProofQuery:
    """What the closing run is given: the target, the plan applied, robocopy's time."""

    target: str
    lines: Sequence[str]
    seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class PushProof:  # pylint: disable=too-many-instance-attributes  # one per line said
    """What the target holds after the run, read back."""

    run_id: str
    target: str  # as Windows writes it
    copied: int = 0
    copied_bytes: int = 0
    failed: tuple[str, ...] = ()  # copies asked for, not found (paths in the target)
    renamed: int = 0  # renames seen made
    unmade: int = 0  # renames asked for, not seen made
    missing: tuple[str, ...] = ()  # PC files the target lacks (paths in the target)
    held: int = 0
    held_bytes: int = 0
    seconds: float = 0.0


def prove_push(runtime: Runtime, query: ProofQuery) -> PushProof:
    """List both sides again; journal what was made.

    Args:
        runtime: Settings, mount points and output.
        query: The target, the plan's lines, robocopy's time.

    Returns:
        What the target holds now.
    """
    target = push_target(runtime, query.target)
    plan = read_plan(query.lines, target)
    run = push_run(runtime.locations.journal_dir, plan.run_id, target)
    sides = list_sides(runtime, target, push_filters(runtime))
    there = {path.casefold(): stat for path, stat in sides.target.items()}
    found = [entry for entry in plan.copies if _there(there, entry)]
    made = record_done(run, _per_folder(sides, found))
    check = ContentCheck(target, tuple(sides.sources))
    broken = BrokenFinder(runtime, check).broken(sides.source)
    missing = tuple(
        path
        for path, stat in sorted(sides.source.items())
        if path not in broken and not _there(there, Entry(path, stat))
    )
    return PushProof(
        run_id=run.run_id,
        target=target.host,
        copied=len(found),
        copied_bytes=sum(entry.stat.size for entry in found),
        failed=tuple(e.path for e in plan.copies if not _there(there, e)),
        renamed=len(made),
        unmade=len(plan.changes) - len(made),
        missing=missing,
        held=len(sides.target),
        held_bytes=sum(stat.size for stat in sides.target.values()),
        seconds=query.seconds,
    )


def _there(there: dict[str, Stat], entry: Entry) -> bool:
    """Tell whether the target holds a file, same size and date.

    Args:
        there: The target's files, by path without case.
        entry: The file.

    Returns:
        True when found as robocopy would leave it.
    """
    stat = there.get(entry.path.casefold())
    return stat is not None and stat.same(entry.stat)


def _per_folder(sides: Sides, copies: list[Entry]) -> dict[str, int]:
    """The bytes copied into each photo folder's folder of the target.

    Args:
        sides: Both sides, with the photo folders taking part.
        copies: The copies found.

    Returns:
        The bytes, by the folder's path in the target.
    """
    copied: dict[str, int] = {}
    for entry in copies:
        for source in sides.sources:
            if entry.path.casefold().startswith(f"{source.prefix}/".casefold()):
                copied[source.prefix] = copied.get(source.prefix, 0) + entry.stat.size
                break
    return copied


def plan_of(runtime: Runtime, query: ProofQuery) -> ReadPlan:
    """Read the plan's lines piped back, for the run that journals them first.

    Args:
        runtime: Settings, mount points and output.
        query: The target and the lines.

    Returns:
        The plan.
    """
    return read_plan(query.lines, push_target(runtime, query.target))
