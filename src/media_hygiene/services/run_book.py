"""Every run of the journal, its facts kept in `/cache`: the home page waits no more.

`status` read every journal in full three times at each home page shown, and asked
the disk file by file whether each run could still be undone: the wait grew with
every run (a minute through Docker Desktop). Now the facts of a run (`run_facts`)
are drawn once and kept in `/cache/journal-facts.json` under the journal's size and
modification time (an append, a rewrite draws them again; a removed journal drops
out), and only the runs of the last `UNDO_WINDOW` days, and the newest, are asked
whether they can be undone (`mh history`, `mh undo <run>` list the others). A "no"
is asked again each time: a quarantine on an unplugged drive looks like a purged one.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Final

from pydantic import TypeAdapter, ValidationError

from media_hygiene.actions.journal_cache import read_journal_once
from media_hygiene.actions.undoable import can_undo
from media_hygiene.constants import JOURNAL_SUFFIX
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.run_facts import RunFacts, acted_on, facts_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.runs import RunSummary
    from media_hygiene.services.runtime import Runtime

FACTS_FILE: Final = "journal-facts.json"
# The runs the home page offers to undo: a week, the newest one always.
UNDO_WINDOW: Final = timedelta(days=7)
_VERSION: Final = 1  # of the file: another one is drawn again


@dataclass(frozen=True, slots=True)
class _Stored:
    """The facts of a run, with the journal version they were drawn from."""

    size: int
    mtime_ns: int
    facts: RunFacts


@dataclass(frozen=True, slots=True)
class _File:
    """`journal-facts.json`."""

    version: int
    runs: dict[str, _Stored]


_ADAPTER: Final = TypeAdapter(_File)


@dataclass(frozen=True, slots=True)
class RunBook:
    """Where the journals are, and where their facts are kept."""

    journal_dir: Path
    store: Path | None  # None: `/cache` is not kept, the facts live this call only


@dataclass(frozen=True, slots=True)
class Runs:
    """The runs, newest first, and those `undo` would still put back."""

    facts: tuple[RunFacts, ...]
    undoable: tuple[RunSummary, ...]


def read_runs(book: RunBook, now: datetime) -> Runs:
    """Read the facts of every run, drawing only those of new or changed journals.

    Args:
        book: The journals and the facts kept.
        now: The moment the window of `undo` ends.

    Returns:
        The runs, newest first, and the undoable ones among the recent.

    Raises:
        JournalError: A changed journal holds a corrupt line, as `status` said before.
    """
    kept = _load(book.store)
    fresh: dict[str, _Stored] = {}
    for file in book.journal_dir.glob(f"*{JOURNAL_SUFFIX}"):
        run_id = file.name.removesuffix(JOURNAL_SUFFIX)
        try:
            stat = file.stat()
        except OSError:  # removed while listed
            continue
        old = kept.get(run_id)
        if old is not None and (old.size, old.mtime_ns) == (
            stat.st_size,
            stat.st_mtime_ns,
        ):
            fresh[run_id] = old
            continue
        facts = facts_of(read_journal_once(file), run_id, stat.st_mtime)
        fresh[run_id] = _Stored(stat.st_size, stat.st_mtime_ns, facts)
    if fresh != kept:
        _save(book.store, fresh)
    ordered = sorted(
        (stored.facts for stored in fresh.values()),
        key=lambda facts: (facts.started, facts.run_id),
        reverse=True,
    )
    return Runs(tuple(ordered), _undoable(book.journal_dir, ordered, now))


def _undoable(
    journal_dir: Path, ordered: list[RunFacts], now: datetime
) -> tuple[RunSummary, ...]:
    """The recent runs, and the newest, that `undo` would still put back.

    Args:
        journal_dir: Journal mount point.
        ordered: Every run, newest first.
        now: The end of the window.

    Returns:
        Their summaries, newest first.
    """
    since = now - UNDO_WINDOW
    recent = [
        facts
        for number, facts in enumerate(ordered)
        if number == 0 or facts.started >= since
    ]
    return tuple(
        facts.summary
        for facts in recent
        if acted_on(facts.summary) and can_undo(journal_dir, facts.run_id)
    )


def _load(store: Path | None) -> dict[str, _Stored]:
    """Read the facts kept; nothing when absent, unreadable or of another version.

    Args:
        store: The file, or None.

    Returns:
        The facts, by run.
    """
    if store is None:
        return {}
    try:
        kept = _ADAPTER.validate_json(store.read_bytes())
    except OSError, ValidationError:
        return {}
    return kept.runs if kept.version == _VERSION else {}


def _save(store: Path | None, runs: dict[str, _Stored]) -> None:
    """Keep the facts, atomically; a failure only costs a read next time.

    Args:
        store: The file, or None.
        runs: The facts, by run.
    """
    if store is None:
        return
    draft = store.with_suffix(".part")
    with contextlib.suppress(OSError):
        draft.write_bytes(_ADAPTER.dump_json(_File(_VERSION, runs)))
        draft.replace(store)


def book_of(runtime: Runtime) -> RunBook:
    """The journals of this runtime, their facts kept when `/cache` is.

    Args:
        runtime: Mount points.

    Returns:
        The book.
    """
    locations = runtime.locations
    kept = runtime.persistent(MountKind.CACHE) and locations.cache_dir.is_dir()
    return RunBook(
        locations.journal_dir, locations.cache_dir / FACTS_FILE if kept else None
    )
