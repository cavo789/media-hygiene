"""What the home page needs of one run, drawn from one read of its journal.

`status` used to read every journal three times at each home page shown (its summary,
whether it can be undone, the newest push) and its quarantine census a fourth: the
wait grew with every run ever made. These facts are taken from a single read and kept
in `/cache` (`run_book`): a run that is over does not change.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states, latest_states
from media_hygiene.actions.kinds import Phase, Status
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.actions.runs import RunSummary, run_phase, summary_of

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry


@dataclass(frozen=True, slots=True)
class PushFacts:
    """A run of `mh push`: whether every rename is done, and where it copied."""

    complete: bool
    host: str | None


@dataclass(frozen=True, slots=True)
class RunFacts:
    """One run, as the home page and `status` see it."""

    started: datetime  # UTC: the first entry, else the journal's last change
    summary: RunSummary
    held: tuple[int, int]  # files still set aside by it, and their bytes
    push: PushFacts | None = None  # None: not a push run
    gone: bool = False  # proven not undoable any more: never checked again

    @property
    def run_id(self) -> str:
        """The run.

        Returns:
            Its identifier.
        """
        return self.summary.run_id


def facts_of(entries: list[JournalEntry], run_id: str, changed: float) -> RunFacts:
    """Draw the facts of a run from its journal.

    Args:
        entries: Its entries, in write order.
        run_id: The run.
        changed: The journal's last change (seconds), when it holds no entry.

    Returns:
        The facts (`gone` left False: `run_book` asks the disk).
    """
    started = entries[0].at if entries else datetime.fromtimestamp(changed, UTC)
    return RunFacts(
        started=started,
        summary=summary_of(entries, run_id),
        held=held_of(entries),
        push=_push_of(entries),
    )


def held_of(entries: list[JournalEntry]) -> tuple[int, int]:
    """Count the files a run set aside and undo did not put back, and their size.

    Args:
        entries: The run's entries.

    Returns:
        How many files, and their size in bytes.
    """
    put_back = {entry.seq for entry in done_states(entries, Phase.UNDO)}
    held = [
        entry
        for entry in done_states(entries, run_phase(entries))
        if entry.action in QUARANTINED and entry.seq not in put_back
    ]
    return len(held), sum(entry.size for entry in held)


def _push_of(entries: list[JournalEntry]) -> PushFacts | None:
    """What a push run did, if it is one.

    Args:
        entries: The run's entries.

    Returns:
        Whether it is complete and where it copied; None for another run.
    """
    pushed = [entry for entry in entries if entry.phase is Phase.PUSH]
    if not pushed:
        return None
    latest = latest_states(entries, Phase.PUSH).values()
    return PushFacts(
        all(entry.status is Status.DONE for entry in latest),
        next((entry.host_path for entry in pushed if entry.host_path), None),
    )


def acted_on(run: RunSummary) -> bool:
    """Tell whether a run changed files that `undo` did not put back yet.

    Args:
        run: A run of the journal.

    Returns:
        True when more files were acted on than restored.
    """
    acted = run.deleted + run.quarantined + run.moved + run.linked
    acted += run.kept.written
    return acted > run.restored
