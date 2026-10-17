"""`media-hygiene xmp`: write the tags into `.xmp` sidecars next to the photos.

The photos themselves are never changed: only small sidecar files that digiKam,
darktable, Lightroom or Immich read. Nothing is written unless asked (`--apply`), and
then like every change of this tool: refused on read-only folders or without a
persistent journal, journaled before each write, read back after, undone by `undo`.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from importlib.metadata import version
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.xmp_write import XmpExecutor
from media_hygiene.constants import APP_NAME
from media_hygiene.index.repository import FactsRepository
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.data_checks import unreadable_index
from media_hygiene.services.journaled_run import new_run
from media_hygiene.services.tag_files import require_index
from media_hygiene.services.xmp_plan import XmpScope, plan_sidecars

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.xmp_plan import XmpPlan


@dataclass(frozen=True, slots=True)
class XmpResult:
    """What an `xmp` run did."""

    run_id: str
    outcome: Outcome
    interrupted: bool


class XmpService:
    """Plans, then writes the sidecars: every write journaled and undoable."""

    def __init__(self, runtime: Runtime, progress: ProgressSink) -> None:
        """Prepare a run.

        Args:
            runtime: Settings, mount points and output.
            progress: Where to report progress.
        """
        self._runtime = runtime
        self._progress = progress

    def ensure_ready(self, *, apply: bool) -> None:
        """Check, before reading anything, that there is an index and a safe place.

        Args:
            apply: The sidecars are to be written: the journal must be mounted and
                the photo folders writable.
        """
        require_index(self._runtime)
        if apply:
            ensure_can_act(self._runtime, Phase.XMP.value)

    def prepare(self, within: tuple[Path, ...]) -> XmpPlan:
        """Decide every sidecar to write, from the index.

        Args:
            within: Container folders (`--path`); empty: every file.

        Returns:
            The plan.

        Raises:
            MountError: The index cannot be read.
        """
        runtime = self._runtime
        scope = XmpScope(
            within,
            tuple(map(runtime.mapper.to_container, runtime.settings.folders.untouched)),
            runtime.settings.tags.xmp_sources,
            f"{APP_NAME} {version(APP_NAME)}",
            runtime.settings.people,
        )
        index = runtime.locations.index_file  # mounted: `ensure_ready` checked it
        try:
            with FactsRepository.open(index) as repository:
                return plan_sidecars(repository.connection, scope)
        except sqlite3.Error as exc:
            raise unreadable_index(runtime, index, exc) from exc

    def execute(self, plan: XmpPlan, stop: Callable[[], bool]) -> XmpResult:
        """Write the sidecars under a new run identifier.

        Args:
            plan: The sidecars.
            stop: Tells when Ctrl+C was pressed: the run stops between two files.

        Returns:
            The run and what it did.
        """
        tally = Tally()
        with new_run(self._runtime, self._progress, Phase.XMP) as context:
            interrupted = XmpExecutor(context, tally).run(plan.jobs, stop)
        run_id = context.quarantine_run_dir.name
        return XmpResult(run_id, tally.freeze(), interrupted)
