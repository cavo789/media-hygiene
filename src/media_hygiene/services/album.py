"""The album use case: an album's folder of hard links on the disk.

An album is the named list of `albums.json` (0298): `album <name>` alone makes its
folder of links, one more use of it. With `--category`, `--event`, `--rule` or
`--rating`, the selection comes instead from the latest classify plan (or the workbook
named), read with the user's edits, and from the index for the stars; each file is
found where the plan saw it, or where a `sort` of that plan moved it. Nothing is
written unless asked (`--apply`), and then every change is journaled and undone by
`undo`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.actions.album import AlbumExecutor, AlbumRun
from media_hygiene.actions.album_plan import plan_links
from media_hygiene.actions.album_stale import leftovers
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.classify.album_rows import chosen_rows
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.album_folder import album_folder
from media_hygiene.services.album_logical import album_files
from media_hygiene.services.album_others import album_index, find_other
from media_hygiene.services.album_picks import find_picks, rated
from media_hygiene.services.journaled_run import new_run
from media_hygiene.services.run_listings import forget_run_listings
from media_hygiene.services.sort_inputs import find_workbook, load_inputs
from media_hygiene.share.album_follow import index_of

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from media_hygiene.actions.album_plan import AlbumPlan, Pick
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
    """An album ready to make: where its files come from, the files, the links."""

    workbook: Path | None  # None: an album of `albums.json`
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
            request: What the user asked: no criterion names an album of
                `albums.json`.

        Returns:
            The album, ready to make.
        """
        if not request.criteria.given:
            return self._from_albums(request.name)
        runtime = self._runtime
        folder = album_folder(runtime, request.name)
        inputs = load_inputs(runtime, find_workbook(runtime, request.workbook))
        rows = chosen_rows(inputs.plan, inputs.edits, request.criteria)
        found, missing = find_picks(runtime, inputs.plan.plan_id, rows)
        picks = rated(runtime, found, request.criteria.rating)
        plan = self._links(folder, picks, missing)
        selected = len(picks) + len(missing)
        return AlbumPrepared(inputs.workbook, selected, plan)

    def _from_albums(self, name: str) -> AlbumPrepared:
        """The folder of links of an album of `albums.json`, named as it is saved.

        Args:
            name: The album's name, whatever its case.

        Returns:
            The album, ready to make.
        """
        found = album_files(self._runtime, name)
        folder = album_folder(self._runtime, found.name)
        plan = self._links(folder, found.picks, found.missing)
        selected = len(found.picks) + len(found.missing)
        return AlbumPrepared(None, selected, plan)

    def _links(
        self, folder: Path, picks: Sequence[Pick], missing: tuple[Path, ...]
    ) -> AlbumPlan:
        """Give each file its name in the album; those of another mount set aside.

        The names of photos taken out of the album since are found too (0374), but
        while a file of the album is not found: its name may be one of them.

        Args:
            folder: The album folder.
            picks: The files found.
            missing: The files not found.

        Returns:
            The links to make, and to remove.
        """
        owner = self._runtime.mounts.owner
        album_mount = owner(folder)
        plan = plan_links(folder, picks, lambda path: owner(path) == album_mount)
        if missing:
            return replace(plan, missing=missing)
        with index_of(album_index(self._runtime)) as connection:
            found = leftovers(folder, picks, find_other(connection, folder))
        return replace(plan, leftovers=found)

    def execute(self, prepared: AlbumPrepared, stop: Callable[[], bool]) -> AlbumResult:
        """Make the album under a new run identifier.

        Args:
            prepared: The album.
            stop: Tells when Ctrl+C was pressed: the run stops between two links.

        Returns:
            The run and what it did.
        """
        tally = Tally()
        with new_run(self._runtime, self._progress, Phase.ALBUM) as context:
            ended = AlbumExecutor(context, tally).run(prepared.plan, stop)
        run_id = context.quarantine_run_dir.name
        forget_run_listings(self._runtime, run_id, Phase.ALBUM)
        return AlbumResult(run_id, tally.freeze(), ended)
