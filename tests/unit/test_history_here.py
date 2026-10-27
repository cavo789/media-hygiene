"""0350: the home server shows the runs in a page, as `mh history` does."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.actions.journal import JournalEntry, JournalWriter
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import RunSummary, list_run_ids, summarize
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.http import Request
from media_hygiene.review.step_watch import HISTORY_PAGE, served_here
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.history_here import HistoryHere, history_page
from media_hygiene.services.history_rows import history_table, undo_line
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

_LOCAL: Final = {"host": "127.0.0.1"}
_RUNS: Final = (
    ("20261011-100000", Phase.CLEAN, ActionKind.QUARANTINE_DUPLICATE),
    ("20261011-100200", Phase.PUSH, ActionKind.MOVE),
    ("20261011-100300", Phase.PHONE, ActionKind.DELETE_DUPLICATE),
)


def _journal(folder: Path) -> None:
    """A clean, an undo, a backup and a phone run."""
    for run_id, phase, action in _RUNS:
        entry = JournalEntry(
            seq=1,
            phase=phase,
            status=Status.DONE,
            action=action,
            path=f"/data/c/{run_id}.jpg",
            host_path=f"C:\\{run_id}.jpg",
            size=2048,
            mtime_ns=1,
            quarantine="/quarantine/x" if "quarantine" in action else None,
        )
        with JournalWriter.open(folder / f"{run_id}.jsonl") as journal:
            journal.record(entry)


def _runs(folder: Path) -> list[RunSummary]:
    return [summarize(folder, run) for run in list_run_ids(folder)]


def test_the_page_says_what_mh_history_says(tmp_path: Path) -> None:
    """Every run, its figures, the notes, and `mh undo <run>` only where it applies."""
    locations = make_locations(tmp_path)
    _journal(locations.journal_dir)
    table = history_table(_runs(locations.journal_dir))
    page = history_page(make_runtime(locations)).decode()
    for row in table.rows:
        assert row.run_id in page
        assert all(cell in page for cell in row.cells)
    assert "mh undo 20261011-100000" in page
    for run in ("100200", "100300"):
        assert f"mh undo 20261011-{run}" not in page
    assert "🛟" in page
    assert "📱" in page
    assert [undo_line(run) for run in _runs(locations.journal_dir)].count("") == 2


def test_without_a_journal_the_page_gives_the_message_and_the_hint(
    tmp_path: Path,
) -> None:
    """The words of `mh history`, in the page, no traceback."""
    runtime = make_runtime(make_locations(tmp_path, MountKind.JOURNAL))
    page = history_page(runtime).decode()
    assert "No journal mount: no history to show." in page
    assert "Mount the journal folder used by clean" in page
    assert "Traceback" not in page


def test_an_empty_journal_says_no_run_yet(tmp_path: Path) -> None:
    """A mounted journal with no run."""
    page = history_page(make_runtime(make_locations(tmp_path))).decode()
    assert "No run yet." in page


@pytest.mark.parametrize(
    ("call", "status"),
    [
        ("GET /history/", 200),
        ("GET /history", 303),
        ("GET /history/x", 404),
        ("POST /history/", 405),
    ],
)
def test_the_route(tmp_path: Path, call: str, status: int) -> None:
    """The page, its redirect, nothing else."""
    runtime = make_runtime(make_locations(tmp_path))
    here = HistoryHere(FreshRuntime(runtime))
    method, path = call.split()
    answer = asyncio.run(here.handle(Request(method, path, _LOCAL, b"")))
    assert answer.status == status


def test_the_step_is_served_here() -> None:
    """`history` is a page of the home server: the click does not leave it."""
    assert served_here(("history",)) == HISTORY_PAGE
