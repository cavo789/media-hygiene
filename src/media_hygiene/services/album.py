"""The album use case: gather a selection of the classify plan as hard links.

The selection comes from the latest classify plan (or the workbook named), read with
the user's edits, and from the index for the stars. Each file is found where the plan
saw it, or where a `sort` of that plan moved it. Nothing is written unless asked
(`--apply`), and then every change is journaled and undone by `undo`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.actions.album import AlbumExecutor, AlbumRun
from media_hygiene.actions.album_plan import plan_links
from media_hygiene.actions.journal import JournalWriter, journal_file
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.runs import new_run_id
from media_hygiene.classify.album_rows import chosen_rows
from media_hygiene.errors import AlbumError
from media_hygiene.i18n import _
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.album_folder import album_folder
from media_hygiene.services.album_picks import find_picks, rated
from media_hygiene.services.sort_inputs import find_workbook, load_inputs

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.actions.album_plan import AlbumPlan
    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.classify.album_rows import Criteria
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class AlbumRequest:
    """What the user asked: the album's name, what it gathers, from which workbook."""

    name: str
    criteria: Criteria
    workbook: str | None = None  # None: the latest classify run's


@dataclass(frozen=True, slots=True)
class AlbumPrepared:
    """An album ready to make: the workbook read, the files selected, the links."""

    workbook: Path
    selected: int
    plan: AlbumPlan


@dataclass(frozen=True, slots=True)
class AlbumResult:
    """What an album run did."""

    run_id: str
    outcome: Outcome
    ended: AlbumRun


class AlbumService:
    """Selects, then links: never a copy, never a move, every link journaled."""

    def __init__(self, runtime: Runtime, progress: ProgressSink) -> None:
        """Prepare an album.

        Args:
            runtime: Settings, mount points and output.
            progress: Where to report progress.
        """
        self._runtime = runtime
        self._progress = progress

    def ensure_ready(self) -> None:
        """Check, before reading anything, that links can be journaled and undone."""
        ensure_can_act(self._runtime, Phase.ALBUM.value)

    def prepare(self, request: AlbumRequest) -> AlbumPrepared:
        """Select the files and give each one its name in the album.

        Args:
            request: What the user asked.

        Returns:
            The album, ready to make.

        Raises:
            AlbumError: Nothing is asked for.
        """
        if not request.criteria.given:
            raise AlbumError(
                _("Say what the album gathers."),
                _("Add --category, --event, --rule or --rating, e.g. --category Noël."),
            )
        runtime = self._runtime
        folder = album_folder(runtime, request.name)
        inputs = load_inputs(runtime, find_workbook(runtime, request.workbook))
        rows = chosen_rows(inputs.plan, inputs.edits, request.criteria)
        found, missing = find_picks(runtime, inputs.plan.plan_id, rows)
        picks = rated(runtime, found, request.criteria.rating)
        owner = runtime.mounts.owner
        album_mount = owner(folder)
        plan = plan_links(folder, picks, lambda path: owner(path) == album_mount)
        selected = len(picks) + len(missing)
        return AlbumPrepared(inputs.workbook, selected, replace(plan, missing=missing))

    def execute(self, prepared: AlbumPrepared, stop: Callable[[], bool]) -> AlbumResult:
        """Make the album under a new run identifier.

        Args:
            prepared: The album.
            stop: Tells when Ctrl+C was pressed: the run stops between two links.

        Returns:
            The run and what it did.
        """
        locations = self._runtime.locations
        locations.journal_dir.mkdir(parents=True, exist_ok=True)
        run_id = new_run_id(locations.journal_dir)
        tally = Tally()
        with JournalWriter.open(journal_file(locations.journal_dir, run_id)) as journal:
            context = CleanContext(
                journal,
                self._runtime.mapper,
                locations.quarantine_dir / run_id,
                self._progress,
                Phase.ALBUM,
            )
            ended = AlbumExecutor(context, tally).run(prepared.plan, stop)
        return AlbumResult(run_id, tally.freeze(), ended)
