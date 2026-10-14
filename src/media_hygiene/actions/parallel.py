"""Run the actions of a clean a few at a time: each one still alone with its journal.

Through a Windows folder seen by Docker, one reader gets ≈ 105 MB/s and four readers
≈ 454 MB/s (measured, TODO 0149): comparing a copy with its kept file, then moving
it, waits on the disk. Each file keeps its own sequence — journal `pending`,
comparison, move, journal `done` — so the comparison stays right before its own
move. Only the screen is updated from the calling thread. Ctrl+C (or `docker stop`)
starts no new file; the files under way end, as one file ended before.
"""

from __future__ import annotations

import logging
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.clean_step import said
from media_hygiene.actions.outcome import Incident

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from media_hygiene.actions.clean_step import Planned
    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.actions.outcome import Tally

_LOGGER = logging.getLogger(__name__)

# Files compared and moved at once: reading scales almost 4 times up to four readers.
WORKERS: Final = 4
# Files handed out ahead of the workers, so that none waits for the next one.
_AHEAD: Final = 2


@dataclass(frozen=True, slots=True)
class Runner:
    """What to do with each planned action, and what to show once it is done."""

    work: Callable[[Planned], None]  # in a worker thread; never raises an OSError
    shown: Callable[[Planned], None]  # in the calling thread, after each action
    workers: int = WORKERS


def run_all(actions: Iterable[Planned], runner: Runner) -> None:
    """Run every action, at most `runner.workers` at a time, in their order of start.

    Args:
        actions: The planned actions.
        runner: The work, the screen update, how many at once.

    Raises:
        BaseException: Ctrl+C, `docker stop` or an unexpected error, raised again
            once the files not started yet are cancelled.
    """
    with ThreadPoolExecutor(runner.workers) as pool:
        running: dict[Future[None], Planned] = {}
        try:
            for planned in actions:
                if len(running) >= runner.workers * _AHEAD:
                    _settle(running, runner, wait(running, return_when=FIRST_COMPLETED))
                running[pool.submit(runner.work, planned)] = planned
            while running:
                _settle(running, runner, wait(running, return_when=FIRST_COMPLETED))
        except BaseException:
            for future in running:
                future.cancel()  # not started yet: never started
            raise


def _settle(
    running: dict[Future[None], Planned],
    runner: Runner,
    finished: tuple[set[Future[None]], set[Future[None]]],
) -> None:
    """Show the actions that ended, and take them off the running ones.

    Args:
        running: The actions handed out, by future.
        runner: How to show one.
        finished: What `wait` returned: the futures done, then the others.
    """
    for future in finished[0]:
        planned = running.pop(future)
        future.result()  # an unexpected error ends the run, as before
        runner.shown(planned)


def guarded(tally: Tally) -> Callable[[Planned], None]:
    """Run an action, an OS error turned into a recorded failure (worker thread).

    Args:
        tally: The counters of the run.

    Returns:
        The work of each action.
    """

    def work(planned: Planned) -> None:
        """Run one action.

        Args:
            planned: The file, what the screen says of it, and the action on it.
        """
        file, _label, action = planned
        try:
            action()
        except OSError as exc:
            _LOGGER.debug("Action failed on %s", file.path, exc_info=True)
            tally.failed.append(Incident(file.path, exc.strerror or str(exc)))

    return work


def shown_on(context: CleanContext) -> Callable[[Planned], None]:
    """Say which file was just handled, and advance the bar by its size.

    Args:
        context: The progress sink and the path mapper of the run.

    Returns:
        The screen update of each action.
    """

    def shown(planned: Planned) -> None:
        """Show one action done.

        Args:
            planned: The file, what the screen says of it, and the action on it.
        """
        context.progress.current(said(planned, context.mapper))
        context.progress.advance(planned[0].size)

    return shown
