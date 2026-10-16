"""The parts of `status`: the quarantine, the reviews not applied, the last proposal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.purge import folder_census, run_folders, runs_in
from media_hygiene.constants import CLASSIFY_PLAN_FILE_NAME
from media_hygiene.errors import DecisionsError
from media_hygiene.report.decisions import BurstStatus, read_decisions
from media_hygiene.review.place import DEFAULT_DECISIONS

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_RUN_STAMP: Final = "%Y%m%d-%H%M%S"
_STAMP_LENGTH: Final = len("20260925-183015")


def run_started(run_id: str) -> datetime:
    """When a run started, from its identifier (local time, as it was named).

    Args:
        run_id: E.g. `20260925-183015` or `20260925-183015-2`.

    Returns:
        An aware moment.
    """
    naive = datetime.strptime(run_id[:_STAMP_LENGTH], _RUN_STAMP)  # noqa: DTZ007
    return naive.astimezone()


@dataclass(frozen=True, slots=True)
class QuarantinedRun:
    """The quarantine of one run: what it holds, since when."""

    run_id: str
    files: int
    size: int
    started: datetime


@dataclass(frozen=True, slots=True)
class QuarantineState:
    """Every run that still has files in the quarantine, newest first."""

    runs: tuple[QuarantinedRun, ...]

    @property
    def files(self) -> int:
        """Count the files of every run.

        Returns:
            Them.
        """
        return sum(run.files for run in self.runs)

    @property
    def size(self) -> int:
        """Sum the size of every run.

        Returns:
            Bytes.
        """
        return sum(run.size for run in self.runs)


def quarantine_state(quarantines: Sequence[Path]) -> QuarantineState:
    """Measure the quarantine of every run, in every quarantine.

    Args:
        quarantines: The default quarantine and the per-drive ones.

    Returns:
        The runs that still hold files.
    """
    runs = (_measure(quarantines, run_id) for run_id in runs_in(quarantines))
    return QuarantineState(tuple(run for run in runs if run.files))


def _measure(quarantines: Sequence[Path], run_id: str) -> QuarantinedRun:
    """Count and measure the quarantine of one run, on every drive.

    Args:
        quarantines: The default quarantine and the per-drive ones.
        run_id: The run.

    Returns:
        Its files, size and start.
    """
    census = [folder_census(folder) for folder in run_folders(quarantines, run_id)]
    return QuarantinedRun(
        run_id,
        sum(files for files, _ in census),
        sum(size for _, size in census),
        run_started(run_id),
    )


@dataclass(frozen=True, slots=True)
class ReviewState:
    """What `decisions.json` holds that no clean applied yet."""

    bursts_to_see: int = 0
    shots_set_aside: int = 0
    near_groups: int = 0  # decided with `review --near`
    unreadable: bool = False


def review_state(reports_dir: Path) -> ReviewState:
    """Read the default decisions file of the reports folder.

    `clean --decisions` renames it once applied: a file still there is not applied.

    Args:
        reports_dir: The reports mount point.

    Returns:
        Its counts; zeros when there is none.
    """
    path = reports_dir / DEFAULT_DECISIONS
    if not path.is_file():
        return ReviewState()
    try:
        decisions = read_decisions(path)
    except DecisionsError:
        return ReviewState(unreadable=True)
    bursts = decisions.bursts
    return ReviewState(
        bursts_to_see=sum(burst.status is BurstStatus.TODO for burst in bursts),
        shots_set_aside=sum(len(burst.discarded) for burst in bursts),
        near_groups=len(decisions.near),
    )


@dataclass(frozen=True, slots=True)
class SortState:
    """The latest `classify` proposal, and whether a sort applied it since."""

    plan: Path | None = None
    proposed: datetime | None = None
    sorted: bool = False


def sort_state(reports_dir: Path, last_sort: str | None) -> SortState:
    """Find the newest `plan.json` and compare it with the newest sort run.

    Args:
        reports_dir: The reports mount point.
        last_sort: The newest sort run not undone, or None.

    Returns:
        The proposal, or an empty state when `classify` never ran.
    """
    plans = sorted(reports_dir.glob(f"*/{CLASSIFY_PLAN_FILE_NAME}"), reverse=True)
    if not plans:
        return SortState()
    proposed = datetime.fromtimestamp(plans[0].stat().st_mtime, UTC)
    applied = last_sort is not None and run_started(last_sort) >= proposed
    return SortState(plans[0], proposed, sorted=applied)
