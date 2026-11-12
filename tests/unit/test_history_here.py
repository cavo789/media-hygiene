"""0350: the home server shows the runs in a page, as `mh history` does."""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import replace
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.actions.journal import JournalEntry, JournalWriter, journal_file
from media_hygiene.actions.journal_copy import journal_copy
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import RunSummary, list_run_ids, summarize
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.review.http import Request
from media_hygiene.review.step_watch import HISTORY_PAGE, served_here
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.history_here import HistoryHere, history_page
from media_hygiene.services.history_rows import history_table, undo_line
from media_hygiene.services.history_runs import load_runs
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

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


def test_a_run_still_in_the_quarantine_has_its_purge_link(tmp_path: Path) -> None:
    """Its files first, by the route of Disk space; no link for the others (0631)."""
    locations = make_locations(tmp_path)
    _journal(locations.journal_dir)
    run_id = _RUNS[0][0]
    aside = locations.quarantine_dir / run_id
    aside.mkdir(parents=True)
    (aside / "a.jpg").write_bytes(b"x")
    page = history_page(make_runtime(locations)).decode()
    assert f'href="/quarantine/?run={run_id}&amp;purge=1&amp;back=history"' in page
    assert page.count("purge=1") == 1


def test_purge_chosen_on_a_page_opens_the_files_of_its_run() -> None:
    """Never a question in the window; `--yes` (the page asked) still runs (0631)."""
    assert served_here(("purge", "20261011-100000")) == (
        "/quarantine/?run=20261011-100000&purge=1"
    )
    assert served_here(("purge", "20261011-100000", "--yes")) is None
    assert served_here(("purge", "--to")) is None


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


def test_a_purge_started_here_lands_back_with_its_read_back(tmp_path: Path) -> None:
    """`?purged=` says what the disk says: gone, or still there (0631)."""
    locations = make_locations(tmp_path)
    _journal(locations.journal_dir)
    run_id = _RUNS[0][0]
    runtime = make_runtime(locations)
    assert "is gone from the quarantine" in history_page(runtime, run_id).decode()
    aside = locations.quarantine_dir / run_id
    aside.mkdir(parents=True)
    (aside / "a.jpg").write_bytes(b"x")
    assert "is still in the quarantine" in history_page(runtime, run_id).decode()
    assert "Read back" not in history_page(runtime).decode()


def _copy_only(locations: Locations, folder: Path | None = None) -> str:
    """The clean run's journal moved beside a quarantine: `/journal` lacks it (0721).

    Returns:
        The run.
    """
    run_id = _RUNS[0][0]
    journal = journal_file(locations.journal_dir, run_id)
    copy = journal_copy(folder or locations.quarantine_dir, run_id)
    copy.parent.mkdir(parents=True, exist_ok=True)
    journal.replace(copy)
    return run_id


def test_a_run_known_only_from_its_quarantine_copy_is_listed_and_marked(
    tmp_path: Path,
) -> None:
    """Journal deleted, copy kept: in `mh history` and the page, with its undo line."""
    locations = make_locations(tmp_path)
    _journal(locations.journal_dir)
    run_id = _copy_only(locations)
    runtime = make_runtime(locations)
    runs = load_runs(runtime)
    assert [run.run_id for run in runs.summaries] == [run for run, *_ in _RUNS][::-1]
    assert runs.copied == {run_id}
    table = history_table(runs.summaries, runs.copied)
    marked = {row.run_id: row for row in table.rows}
    assert marked[run_id].source == "from the quarantine"
    assert marked[run_id].undo == f"mh undo {run_id}"  # undo takes the copy back
    assert not [row for row in table.rows if row.source and row.run_id != run_id]
    assert any(note.startswith("🧾") for note in table.notes)
    page = history_page(runtime).decode()
    assert "from the quarantine" in page
    assert f"mh undo {run_id}" in page
    assert not journal_file(locations.journal_dir, run_id).exists()  # read-only


def test_a_run_with_both_journal_and_copy_is_listed_once_unmarked(
    tmp_path: Path,
) -> None:
    """The journal is the reference; its copy beside the quarantine adds nothing."""
    locations = make_locations(tmp_path)
    _journal(locations.journal_dir)
    run_id = _RUNS[0][0]
    journal = journal_file(locations.journal_dir, run_id)
    journal_copy(locations.quarantine_dir, run_id).write_bytes(journal.read_bytes())
    runs = load_runs(make_runtime(locations))
    assert [run.run_id for run in runs.summaries].count(run_id) == 1
    assert not runs.copied
    table = history_table(runs.summaries, runs.copied)
    assert not any(row.source for row in table.rows)
    assert not any(note.startswith("🧾") for note in table.notes)


def test_a_drive_quarantine_counts_only_when_mounted(tmp_path: Path) -> None:
    """E:'s copy: read from its mount; Docker's empty `e` folder invents nothing."""
    locations = make_locations(tmp_path)
    _journal(locations.journal_dir)
    own = locations.quarantine_dir / "e"
    run_id = _copy_only(locations, own)
    runtime = make_runtime(locations)
    assert run_id not in {run.run_id for run in load_runs(runtime).summaries}
    assert "Traceback" not in history_page(runtime).decode()
    mounted = replace(runtime, mounts=MountTable(frozenset({own})))
    assert load_runs(mounted).copied == {run_id}


def test_an_unreadable_copy_or_quarantine_invents_no_run(tmp_path: Path) -> None:
    """A corrupt copy, a quarantine folder missing: the other runs, no traceback."""
    locations = make_locations(tmp_path)
    _journal(locations.journal_dir)
    run_id = _copy_only(locations)
    journal_copy(locations.quarantine_dir, run_id).write_text("{not json\n", "utf-8")
    runtime = make_runtime(locations)
    assert len(load_runs(runtime).summaries) == len(_RUNS) - 1
    assert run_id not in history_page(runtime).decode()
    shutil.rmtree(locations.quarantine_dir)
    assert len(load_runs(runtime).summaries) == len(_RUNS) - 1
