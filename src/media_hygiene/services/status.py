"""Where am I? What the tool's own folders say, read without scanning anything.

The reports give the last audit or clean, the journal the runs still undoable, the
quarantine what still takes space, `decisions.json` the reviews not applied yet and the
latest `plan.json` a proposal not sorted yet. A tool folder that is not mounted is
reported as not looked at: the command never fails for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.runs import RunSummary, list_run_ids, summarize
from media_hygiene.actions.undoable import can_undo
from media_hygiene.index.face_coverage import face_coverage
from media_hygiene.index.tag_rows import tag_coverage
from media_hygiene.index.walks import last_walk
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.report.index_page import load_summaries
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.status_parts import (
    QuarantineState,
    ReviewState,
    SortState,
    quarantine_state,
    review_state,
    sort_state,
)

if TYPE_CHECKING:
    from media_hygiene.report.summary import ReportSummary
    from media_hygiene.services.runtime import Runtime

_STAMP: Final = "%Y%m%d-%H%M%S"  # a run's identifier starts with it
_STAMP_LENGTH: Final = 15
# The tool folders `status` reads; the photos are never needed.
LOOKED_AT: Final = (
    MountKind.REPORTS,
    MountKind.JOURNAL,
    MountKind.QUARANTINE,
    MountKind.CACHE,
)


@dataclass(frozen=True, slots=True)
class LastAnalysis:
    """The newest audit or clean: its report, or only the date the cache knows."""

    summary: ReportSummary | None
    walked: datetime | None  # from the index, when no report tells

    @property
    def seen(self) -> bool:
        """Tell whether any audit ran.

        Returns:
            True when a report or the cache knows one.
        """
        return self.summary is not None or self.walked is not None


# One field per part of the screen: the record mirrors what `status` shows.
@dataclass(frozen=True, slots=True)
class Status:  # pylint: disable=too-many-instance-attributes
    """Everything `status` shows, and what it could not look at."""

    analysis: LastAnalysis
    undoable: tuple[RunSummary, ...]  # newest first
    quarantine: QuarantineState
    review: ReviewState
    sort: SortState
    missing: tuple[MountKind, ...]
    # Files with words, and with the vision model's; None before any `tags`.
    tagged: tuple[int, int] | None = None
    # Photos analysed and faces found; None before any `people`.
    faces: tuple[int, int] | None = None
    imported: str | None = None  # the newest `import` run (0265)
    backed_up: datetime | None = None  # when the newest `mh backup` ran (0264)

    @property
    def blank(self) -> bool:
        """Tell whether the tool folders know of nothing done yet.

        Returns:
            True without any audit, run, quarantine, review or proposal.
        """
        return not (
            self.analysis.seen
            or self.undoable
            or self.quarantine.runs
            or self.review != ReviewState()
            or self.sort.proposed is not None
        )


def read_status(runtime: Runtime) -> Status:
    """Read the tool folders: reports, journal, quarantine, cache.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The state; empty parts for the folders not mounted.
    """
    locations = runtime.locations
    mounted = {kind for kind in LOOKED_AT if runtime.persistent(kind)}
    summaries = (
        load_summaries(locations.reports_dir)
        if MountKind.REPORTS in mounted and locations.reports_dir.is_dir()
        else []
    )
    runs = (
        tuple(
            summarize(locations.journal_dir, run)
            for run in list_run_ids(locations.journal_dir)
        )
        if MountKind.JOURNAL in mounted
        else ()
    )
    reports = MountKind.REPORTS in mounted
    return Status(
        analysis=LastAnalysis(
            summaries[0] if summaries else None,
            last_walk(runtime.index_file),
        ),
        undoable=tuple(
            run
            for run in runs
            if _undoable(run) and can_undo(locations.journal_dir, run.run_id)
        ),
        quarantine=quarantine_state(
            mounted_quarantines(runtime).folders, locations.journal_dir
        )
        if MountKind.QUARANTINE in mounted
        else QuarantineState(()),
        review=review_state(locations.reports_dir) if reports else ReviewState(),
        sort=sort_state(locations.reports_dir, _last_sort(runs))
        if reports
        else SortState(),
        missing=tuple(kind for kind in LOOKED_AT if kind not in mounted),
        tagged=tag_coverage(runtime.index_file),
        faces=face_coverage(runtime.index_file),
        imported=next((r.run_id for r in runs if r.kind is Phase.IMPORT), None),
        backed_up=_started(
            next((r.run_id for r in runs if r.kind is Phase.BACKUP), "")
        ),
    )


def _started(run_id: str) -> datetime | None:
    """When a run started, from its identifier (local time).

    Args:
        run_id: The run, or empty.

    Returns:
        The moment, aware; None for no run.
    """
    if not run_id:
        return None
    return datetime.strptime(run_id[:_STAMP_LENGTH], _STAMP).astimezone()


def _undoable(run: RunSummary) -> bool:
    """Tell whether a run changed files that `undo` did not put back yet.

    Args:
        run: A run of the journal.

    Returns:
        True when more files were acted on than restored.
    """
    acted = run.deleted + run.quarantined + run.moved + run.linked
    acted += run.kept.written
    return acted > run.restored


def _last_sort(runs: tuple[RunSummary, ...]) -> str | None:
    """The newest sort run, not undone.

    Args:
        runs: The runs, newest first.

    Returns:
        Its identifier, or None.
    """
    return next(
        (run.run_id for run in runs if run.kind is Phase.SORT and _undoable(run)),
        None,
    )
