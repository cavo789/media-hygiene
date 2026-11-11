"""The slow facts of *Are my photos safe?* kept in /cache (0692): one test per event."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.journal import JournalEntry, journal_file
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.cli.status_safety import page_safety, safety_of
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.home_more_api import SAFETY_PATH, HomeMore, more_response
from media_hygiene.review.home_paths import HOME_PATHS
from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import READ_PATHS
from media_hygiene.services import safety_cache
from media_hygiene.services.only_copies import only_copies
from media_hygiene.services.safety_cache import (
    SAFETY_CACHE_NAME,
    SlowAsk,
    SlowFacts,
    slow_facts,
)
from media_hygiene.services.status import read_status
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_RUN = "20261101-120000"
_OTHER = "20261102-120000"


def _runtime(tmp_path: Path, *missing: MountKind) -> Runtime:
    """A runtime whose quarantine is never old."""
    return make_runtime(
        make_locations(tmp_path, *missing), {"clean": {"purge_hint_days": 100_000}}
    )


def _clean(runtime: Runtime, run: str, files: int) -> None:
    """A clean run that set `files` exact copies aside; the first one's twin is gone."""
    locations = runtime.locations
    photos = locations.data_dir / "c" / "Photos"
    photos.mkdir(parents=True, exist_ok=True)
    lines = []
    for number in range(files):
        keeper = photos / f"{run}-{number}.jpg"
        if number:
            keeper.write_bytes(b"xx")
        aside = locations.quarantine_dir / run / "c" / "d" / f"{number}.jpg"
        aside.parent.mkdir(parents=True, exist_ok=True)
        aside.write_bytes(b"xx")
        entry = JournalEntry(
            seq=number,
            phase=Phase.CLEAN,
            status=Status.PENDING,
            action=ActionKind.QUARANTINE_DUPLICATE,
            path=f"/data/c/{number}.jpg",
            host_path=f"C:\\{number}.jpg",
            size=2,
            mtime_ns=0,
            keeper=str(keeper),
            quarantine=str(aside),
        )
        lines += [entry.model_dump_json(), entry.as_done().model_dump_json()]
    journal_file(locations.journal_dir, run).write_text("\n".join(lines) + "\n")


class _Counted:
    """Counts the reads of only_copies (a read: the cache missed)."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.reads = 0
        real = only_copies

        def counted(*args: object) -> object:
            self.reads += 1
            return real(*args)  # type: ignore[arg-type]

        monkeypatch.setattr(f"{safety_cache.__name__}.only_copies", counted)


def _ask(runtime: Runtime, *runs: str) -> SlowAsk:
    """The question, with the default quarantine only."""
    return SlowAsk(runtime, runs, (runtime.locations.quarantine_dir,))


@pytest.fixture
def counted(monkeypatch: pytest.MonkeyPatch) -> _Counted:
    """The reads counted."""
    return _Counted(monkeypatch)


def test_second_call_reads_the_cache(tmp_path: Path, counted: _Counted) -> None:
    """Nothing changed: the facts come from /cache, the same ones."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    first = slow_facts(_ask(runtime, _RUN))
    assert first == SlowFacts(1, ())
    assert slow_facts(_ask(runtime, _RUN)) == first
    assert counted.reads == 1
    assert (runtime.locations.cache_dir / SAFETY_CACHE_NAME).is_file()


def test_card_is_the_same_cached_or_not(tmp_path: Path) -> None:
    """Equivalence: the card read twice (the second from the cache) says the same."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    first = page_safety(runtime)
    assert page_safety(runtime) == first
    lines = safety_of(runtime, read_status(runtime))
    assert [row.sub for row in first.rows] == [line.sub for line in lines]
    assert "1 file exists nowhere else" in first.rows[4].sub


def test_a_new_run_reads_again(tmp_path: Path, counted: _Counted) -> None:
    """A clean adds a run."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    slow_facts(_ask(runtime, _RUN))
    _clean(runtime, _OTHER, 2)
    assert slow_facts(_ask(runtime, _RUN, _OTHER)).only == 2
    assert counted.reads == 2


def test_undo_reads_again(tmp_path: Path, counted: _Counted) -> None:
    """An undo appends to the journal and takes files out of the quarantine."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    slow_facts(_ask(runtime, _RUN))
    file = journal_file(runtime.locations.journal_dir, _RUN)
    with file.open("a", encoding="utf-8") as journal:
        journal.write("\n")
    slow_facts(_ask(runtime, _RUN))
    assert counted.reads == 2


def test_purge_reads_again(tmp_path: Path, counted: _Counted) -> None:
    """A purge removes the run's folder: the run leaves the list."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    _clean(runtime, _OTHER, 2)
    slow_facts(_ask(runtime, _RUN, _OTHER))
    shutil.rmtree(runtime.locations.quarantine_dir / _RUN)
    assert slow_facts(_ask(runtime, _OTHER)).only == 1
    assert counted.reads == 2


def test_file_removed_by_hand_reads_again(tmp_path: Path, counted: _Counted) -> None:
    """A file deleted from the quarantine in Explorer: its folder's mtime changes."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    assert slow_facts(_ask(runtime, _RUN)).only == 1
    folder = runtime.locations.quarantine_dir / _RUN / "c" / "d"
    (folder / "0.jpg").unlink()
    os.utime(folder, ns=(1, 1))  # a coarse clock would keep the same mtime
    assert slow_facts(_ask(runtime, _RUN)).only == 0
    assert counted.reads == 2


def test_drive_quarantine_mounted_reads_again(
    tmp_path: Path, counted: _Counted
) -> None:
    """A drive's quarantine plugged in (then out) changes the quarantines mounted."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    default = runtime.locations.quarantine_dir
    drive = default / "e"
    drive.mkdir()
    slow_facts(_ask(runtime, _RUN))
    slow_facts(SlowAsk(runtime, (_RUN,), (default, drive)))
    slow_facts(_ask(runtime, _RUN))
    assert counted.reads == 3


def test_journal_restored_reads_again(tmp_path: Path, counted: _Counted) -> None:
    """A journal put back by `mh backup` (a copy keeping the mtime): its ctime moves."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    slow_facts(_ask(runtime, _RUN))
    file = journal_file(runtime.locations.journal_dir, _RUN)
    copy = tmp_path / "saved.jsonl"
    shutil.copy2(file, copy)
    file.unlink()
    shutil.copy2(copy, file)  # same size, same mtime, a new file
    slow_facts(_ask(runtime, _RUN))
    assert counted.reads == 2


def test_lost_journal_reads_again(tmp_path: Path, counted: _Counted) -> None:
    """A journal lost: every file of its run counts as an only copy."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    slow_facts(_ask(runtime, _RUN))
    journal_file(runtime.locations.journal_dir, _RUN).unlink()
    assert slow_facts(_ask(runtime, _RUN)).only == 3
    assert counted.reads == 2


def test_audit_after_twin_removed_reads_again(
    tmp_path: Path, counted: _Counted
) -> None:
    """A kept twin removed by hand is seen once an audit writes the index."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    slow_facts(_ask(runtime, _RUN))
    (runtime.locations.data_dir / "c" / "Photos" / f"{_RUN}-1.jpg").unlink()
    runtime.locations.index_file.write_bytes(b"audited")
    assert slow_facts(_ask(runtime, _RUN)).only == 2
    assert counted.reads == 2


def test_broken_cache_reads_again(tmp_path: Path, counted: _Counted) -> None:
    """A cache file that does not load is read past."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    (runtime.locations.cache_dir / SAFETY_CACHE_NAME).write_text("{", "utf-8")
    assert slow_facts(_ask(runtime, _RUN)).only == 1
    assert counted.reads == 1


def test_no_cache_mount_reads_each_time(tmp_path: Path, counted: _Counted) -> None:
    """Without a persistent /cache nothing is kept."""
    runtime = _runtime(tmp_path, MountKind.CACHE)
    _clean(runtime, _RUN, 3)
    slow_facts(_ask(runtime, _RUN))
    slow_facts(_ask(runtime, _RUN))
    assert counted.reads == 2


def test_the_route_answers_the_card(tmp_path: Path) -> None:
    """`GET /api/safety` sends the card; a phone may read it too; absent: no answer."""
    runtime = _runtime(tmp_path)
    _clean(runtime, _RUN, 3)
    more = HomeMore(safety=lambda: page_safety(runtime))
    get = Request("GET", SAFETY_PATH, {"host": "127.0.0.1"}, b"")
    answer = asyncio.run(more_response(more, get))
    assert answer is not None
    assert answer.status == HTTPStatus.OK
    assert json.loads(answer.body)["title"] == "Are my photos safe?"
    assert asyncio.run(more_response(HomeMore(), get)) is None
    assert SAFETY_PATH in READ_PATHS
    assert SAFETY_PATH in HOME_PATHS
