"""Turn the photos `people` proposes to straighten, journaled and undoable (0802).

The photos proposed (`index.turn_rows`), but those refused on the page
(`index.turn_refusals`), those of a protected folder or a backup (never written) and
any file not a JPEG (only a JPEG's two orientation bytes are changed). The run is like
every change of this tool: refused on read-only folders or without a persistent
journal, journaled before each write, read back after, undone by `undo`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.turn_write import TurnExecutor, TurnJob
from media_hygiene.faces.models import FACE_MODEL
from media_hygiene.faces.straighten import ORIENTATION_OF, Turn
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.turn_refusals import TurnRefusals
from media_hygiene.index.turn_rows import TurnStore
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.journaled_run import new_run

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Sequence
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime

_JPEG: Final = frozenset({".jpg", ".jpeg"})


@dataclass(frozen=True, slots=True)
class TurnScope:
    """What is never turned: the photos refused and the folders never written."""

    refused: Collection[Path]
    untouched: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class TurnResult:
    """What a run did."""

    run_id: str
    outcome: Outcome
    interrupted: bool


def turn_jobs(
    proposed: Sequence[tuple[Path, int]], scope: TurnScope
) -> tuple[TurnJob, ...]:
    """The photos to turn, and the orientation code each gets.

    Args:
        proposed: Each photo and its turn in degrees clockwise.
        scope: The refusals and the folders never written.

    Returns:
        The jobs, in the order proposed.
    """
    return tuple(
        TurnJob(path, ORIENTATION_OF[Turn(turn)])
        for path, turn in proposed
        if Turn(turn) in ORIENTATION_OF
        and path.suffix.lower() in _JPEG
        and path not in scope.refused
        and not any(path.is_relative_to(folder) for folder in scope.untouched)
    )


class TurnService:
    """Lists, then writes the turns: every write journaled and undoable."""

    def __init__(self, runtime: Runtime, progress: ProgressSink) -> None:
        """Prepare a run.

        Args:
            runtime: Settings, mount points and output.
            progress: Where to report progress.
        """
        self._runtime = runtime
        self._progress = progress

    def prepare(self) -> tuple[TurnJob, ...]:
        """The photos to turn now, from the index.

        Returns:
            The jobs.
        """
        runtime = self._runtime
        mapper = runtime.mapper
        untouched = tuple(map(mapper.to_container, runtime.settings.folders.untouched))
        with FactsRepository.open(runtime.locations.index_file) as repository:
            connection = repository.connection
            proposed = TurnStore(connection, FACE_MODEL).proposed()
            refused = TurnRefusals(connection).refused()
        return turn_jobs(proposed, TurnScope(refused, untouched))

    def execute(self, jobs: Sequence[TurnJob], stop: Callable[[], bool]) -> TurnResult:
        """Turn the photos under a new run identifier.

        Args:
            jobs: The photos.
            stop: Tells when Ctrl+C was pressed: the run stops between two photos.

        Returns:
            The run and what it did.
        """
        ensure_can_act(self._runtime, Phase.TURN.value)
        tally = Tally()
        with new_run(self._runtime, self._progress, Phase.TURN) as context:
            interrupted = TurnExecutor(context, tally).run(jobs, stop)
        run_id = context.quarantine_run_dir.name
        return TurnResult(run_id, tally.freeze(), interrupted)
