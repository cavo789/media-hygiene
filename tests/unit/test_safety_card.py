"""*Are my photos safe?* (0689): the card's lines read from disk, in each state."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.cli.home_state import home_state
from media_hygiene.cli.safety_lines import Level
from media_hygiene.cli.status_safety import safety_of, show_safety
from media_hygiene.index.safety_counts import RereadCounts, newer_than, reread_counts
from media_hygiene.index.verified_rows import CREATE_VERIFIED
from media_hygiene.services.safety_records import last_backup, off_pc
from media_hygiene.services.status import read_status
from tests.support.home_states import (
    after_clean,
    all_safe,
    first_run,
    old_push,
)
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_G, _W, _B, _U = Level.GOOD, Level.WARN, Level.BAD, Level.UNKNOWN
# Per state: copy, off the PC, memory, way back, quarantine, damaged, re-read, drill.
_EXPECTED: Final[dict[str, tuple[Callable[[Runtime], None], tuple[Level, ...]]]] = {
    "no target": (first_run, (_B, _U, _B, _G, _G, _U, _U, _U)),
    "old push": (old_push, (_W, _G, _B, _G, _G, _U, _U, _U)),
    "everything green": (all_safe, (_G, _G, _G, _G, _G, _U, _U, _U)),
}


def _runtime(tmp_path: Path) -> Runtime:
    """A runtime whose quarantine is never old."""
    return make_runtime(
        make_locations(tmp_path), {"clean": {"purge_hint_days": 100_000}}
    )


@pytest.mark.parametrize("state", list(_EXPECTED))
def test_levels_of_each_state(tmp_path: Path, state: str) -> None:
    """Each line's level, read from what the tool folders hold."""
    situation, levels = _EXPECTED[state]
    runtime = _runtime(tmp_path)
    situation(runtime)
    lines = safety_of(runtime, read_status(runtime))
    assert tuple(line.level for line in lines) == levels


def test_quarantine_counts_only_copies(tmp_path: Path) -> None:
    """A file set aside with no journal entry naming a twin is an only copy."""
    runtime = _runtime(tmp_path)
    after_clean(runtime)
    index = runtime.index_file
    assert index is not None
    indexed_photos(index, tmp_path / "none", 0)  # the count reads the index
    line = safety_of(runtime, read_status(runtime))[4]
    assert "1 file exists nowhere else" in line.sub
    assert line.step == "purge"


def test_home_state_carries_the_card(tmp_path: Path) -> None:
    """The page's state holds the card, the steps that fix it named."""
    runtime = _runtime(tmp_path)
    old_push(runtime)
    safety = home_state(runtime).safety
    assert safety is not None
    assert [row.level for row in safety.rows][:3] == ["warn", "good", "bad"]
    assert safety.rows[2].action == "backup"


def test_status_prints_the_card(tmp_path: Path) -> None:
    """`mh status` prints the same lines, one mark each."""
    runtime = _runtime(tmp_path)
    first_run(runtime)
    show_safety(runtime, read_status(runtime))  # no error without any record


@pytest.mark.parametrize(
    ("host", "away"),
    [
        (r"\\NAS\share\C", True),
        (r"E:\Backup", True),
        (r"C:\Users\me", False),
        ("/home/me", None),
        (None, None),
    ],
)
def test_off_pc(host: str | None, away: bool | None) -> None:  # noqa: FBT001
    """A share or another drive is off this PC; `C:` is not; Linux is unknown."""
    assert off_pc(host) is away


def test_unreadable_backup_note_is_none(tmp_path: Path) -> None:
    """A note that does not read is no backup."""
    (tmp_path / "backup-made.json").write_text("{", "utf-8")
    assert last_backup(tmp_path) is None


def test_reread_and_damaged_lines(tmp_path: Path) -> None:
    """The re-read's progress and the damaged files come from the index (0690)."""
    runtime = _runtime(tmp_path)
    index = runtime.locations.index_file
    index.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(index) as connection:
        connection.execute("CREATE TABLE files (path TEXT, mtime_ns INTEGER)")
        connection.executemany(
            "INSERT INTO files VALUES (?, 0)", [("a",), ("b",), ("c",), ("d",)]
        )
        connection.execute(CREATE_VERIFIED)
        connection.execute(
            "INSERT INTO verified VALUES ('a', 1, 0, 'x', '2026-11-01', '2026-11-02',"
            " 'y')"
        )
    connection.close()
    counts = reread_counts(index)
    assert counts == RereadCounts(4, 1, 1, "2026-11-01")
    lines = safety_of(runtime, read_status(runtime))
    assert (lines[5].level, lines[6].level) == (Level.BAD, Level.GOOD)
    assert "1 of 4 files (25 %)" in lines[6].sub
    assert newer_than(index, -1) == 4


def test_index_without_reread_and_missing_index(tmp_path: Path) -> None:
    """An index older than the re-read counts nothing read; no index is unknown."""
    assert reread_counts(None) is None
    assert newer_than(None, 0) is None
    index = tmp_path / "index.sqlite"
    with sqlite3.connect(index) as connection:
        connection.execute("CREATE TABLE files (path TEXT)")
    connection.close()
    assert reread_counts(index) == RereadCounts(0, 0, 0, None)
    assert newer_than(index, 0) is None  # no mtime column: unreadable, unknown
