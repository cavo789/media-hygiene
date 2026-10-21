"""`mh backup`'s plan, in the container: the sources against the target (0264).

Read-only: the photo folders and the target are listed (size, date), a few files read
(128 KiB each) to prove a move, the index and the journals read. Only the sources
listed whole take part: a folder the walk could not read leaves its part of the target
untouched. Windows applies the plan (`mh_backup.ps1.j2`); `backup_proof` proves it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.runs import RUN_ID_PATTERN, new_run_id
from media_hygiene.plan.backup_target import BackupInputs, BackupPlan, plan_backup
from media_hygiene.scan.filters import ScanFilters
from media_hygiene.scan.skipped_dirs import SYSTEM_DIR_NAMES
from media_hygiene.services.backup_broken import BrokenFinder, ContentCheck
from media_hygiene.services.backup_listing import list_tree
from media_hygiene.services.backup_place import REMOVED_FOLDER, Target
from media_hygiene.services.backup_reasons import gone_reasons
from media_hygiene.services.backup_sources import (
    Source,
    backup_sources,
    backup_target,
)

if TYPE_CHECKING:
    from pathlib import Path, PurePosixPath

    from media_hygiene.plan.backup_entries import Stat
    from media_hygiene.services.runtime import Runtime

_STAMP: Final = "%Y%m%d-%H%M%S"
_STAMP_LENGTH: Final = 15


@dataclass(frozen=True, slots=True)
class Skipped:
    """A photo folder left out this run: the walk could not read all of it."""

    host: str
    unreadable: int


@dataclass(frozen=True, slots=True)
class Prepared:  # pylint: disable=too-many-instance-attributes  # one per plan line
    """The plan of a run, and what Windows needs to apply it."""

    target: Target
    run_id: str
    plan: BackupPlan
    sources: tuple[Source, ...] = ()  # taking part
    skipped: tuple[Skipped, ...] = ()
    expired: tuple[str, ...] = ()  # `.removed/<run>` folders older than kept
    excluded: tuple[str, ...] = ()  # robocopy `/XD`: names, host paths
    stopped: bool = False
    threads: int = 1
    keep_days: int = 0  # `[backup] keep_removed_days`
    stop_percent: int = 0  # `[backup] stop_above_percent`


@dataclass(frozen=True, slots=True)
class Sides:
    """Both sides of the sources taking part, by path relative to the target."""

    source: dict[str, Stat] = field(default_factory=dict)
    target: dict[str, Stat] = field(default_factory=dict)
    sources: list[Source] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)


def prepare_backup(runtime: Runtime, target_host: str, *, anyway: bool) -> Prepared:
    """Compare the photo folders with the target.

    Args:
        runtime: Settings, mount points and output.
        target_host: The target as typed.
        anyway: `--anyway`: the safety stop does not stop.

    Returns:
        The plan.
    """
    target = backup_target(runtime, target_host)
    filters = backup_filters(runtime)
    sides = list_sides(runtime, target, filters)
    check = ContentCheck(target, tuple(sides.sources))
    on_pc = {path.casefold() for path in sides.source}
    gone = {
        path: check.pc_path(path)
        for path in sides.target
        if path.casefold() not in on_pc
    }
    inputs = BackupInputs(
        sides.source,
        sides.target,
        broken=BrokenFinder(runtime, check).broken(sides.source),
        reasons=gone_reasons(runtime, gone),
    )
    plan = plan_backup(inputs, check.same)
    settings = runtime.settings.backup
    return Prepared(
        target=target,
        run_id=new_run_id(runtime.locations.journal_dir),
        plan=plan,
        sources=tuple(sides.sources),
        skipped=tuple(sides.skipped),
        expired=_expired(target, settings.keep_removed_days),
        excluded=(
            *SYSTEM_DIR_NAMES,
            *runtime.settings.scan.excluded_names,
            *runtime.settings.folders.excluded,
        ),
        stopped=not anyway and plan.stops(settings.stop_above_percent),
        threads=settings.threads,
        keep_days=settings.keep_removed_days,
        stop_percent=settings.stop_above_percent,
    )


def list_sides(runtime: Runtime, target: Target, filters: ScanFilters) -> Sides:
    """List each photo folder and its folder in the target; skip one read in part.

    Args:
        runtime: Settings, mount points and output.
        target: The target.
        filters: The folders skipped on both sides.

    Returns:
        Both sides of the folders listed whole.
    """
    sides = Sides()
    for source in backup_sources(runtime, target):

        def skips(below: PurePosixPath, point: Path = source.point) -> bool:
            """Skip a folder skipped on the PC, on both sides.

            Args:
                below: The folder, relative to the photo folder.
                point: The photo folder.

            Returns:
                True for a system, excluded or excluded-name folder.
            """
            return filters.skips_dir(point / below)

        pc = list_tree(source.point, source.prefix, skips)
        there = list_tree(target.point / source.prefix, source.prefix, skips)
        unreadable = len(pc.unreadable) + len(there.unreadable)
        if unreadable:
            sides.skipped.append(Skipped(source.host, unreadable))
            continue
        sides.sources.append(source)
        sides.source.update(pc.files)
        sides.target.update(there.files)
    return sides


def backup_filters(runtime: Runtime) -> ScanFilters:
    """The folders skipped: system names, `[scan] excluded_names`, `[folders] excluded`.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Filters skipping folders only: every file of the others counts.
    """
    settings = runtime.settings
    return ScanFilters(
        excluded=tuple(
            runtime.mapper.to_container(folder) for folder in settings.folders.excluded
        ),
        excluded_names=settings.scan.excluded_names,
    )


def _expired(target: Target, days: int) -> tuple[str, ...]:
    """The folders of `.removed` older than `[backup] keep_removed_days`.

    Args:
        target: The target.
        days: How long a run's folder is kept.

    Returns:
        Their paths relative to the target, oldest first.
    """
    removed = target.point / REMOVED_FOLDER
    if not removed.is_dir():
        return ()
    limit = datetime.now().astimezone() - timedelta(days=days)
    expired: list[str] = []
    for folder in sorted(removed.iterdir()):
        if not folder.is_dir() or not RUN_ID_PATTERN.fullmatch(folder.name):
            continue
        stamp = datetime.strptime(folder.name[:_STAMP_LENGTH], _STAMP).astimezone()
        if stamp < limit:
            expired.append(f"{REMOVED_FOLDER}/{folder.name}")
    return tuple(expired)
