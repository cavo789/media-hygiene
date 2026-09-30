"""An interrupted sort, run again: every row moved once, none reported missing."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.runs import list_run_ids
from tests.support.runtime import make_runtime
from tests.support.sorting import (
    build_library,
    classify,
    folders,
    name_first_event,
    snapshot,
    sort,
    undo,
)

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_BEFORE_KILL = 3


def moved_rows(locations: Locations) -> list[str]:
    """The rows every run moved, once per move."""
    rows: list[str] = []
    for run_id in list_run_ids(locations.journal_dir):
        entries = read_journal(journal_file(locations.journal_dir, run_id))
        done = [e for e in entries if e.action is ActionKind.MOVE and e.row]
        rows += [e.row or "" for e in done if e.status.value == "done"]
    return rows


def test_a_killed_sort_resumes_where_it_stopped(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Killed after three moves: the second run moves the rest, nothing is missing."""
    build_library(locations.data_dir)
    start, tree = snapshot(locations.data_dir), folders(locations.data_dir)
    runtime = make_runtime(locations)
    name_first_event(classify(runtime))
    rename = Path.rename
    calls: list[Path] = []

    def dying(self: Path, target: Path) -> Path:
        calls.append(self)
        if len(calls) > _BEFORE_KILL:
            raise KeyboardInterrupt
        return rename(self, target)

    monkeypatch.setattr(Path, "rename", dying)
    with pytest.raises(KeyboardInterrupt):
        sort(runtime)
    monkeypatch.setattr(Path, "rename", rename)
    second = sort(runtime)
    assert not second.moves.outcome.skipped  # nothing reported missing
    assert not second.moves.outcome.failed
    assert second.manifest.intact
    rows = moved_rows(locations)
    assert len(rows) == len(set(rows))  # every row moved once
    for run_id in list_run_ids(locations.journal_dir):  # newest first
        assert not undo(runtime, run_id).failed
    assert snapshot(locations.data_dir) == start
    assert folders(locations.data_dir) == tree


def test_ctrl_c_finishes_the_file_then_a_new_run_continues(
    locations: Locations,
) -> None:
    """Asked to stop: the group ends, no folder is removed yet, the next run ends it."""
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    name_first_event(classify(runtime))
    asked = iter([False, False, True])
    first = sort(runtime, stop=lambda: next(asked, True))
    assert first.moves.interrupted
    assert first.moves.moved
    assert first.folders.removed == 0
    second = sort(runtime)
    assert not second.moves.interrupted
    assert not second.moves.outcome.skipped
    assert second.folders.removed >= 2  # the folders the first run emptied, too
    third = sort(runtime)
    assert not third.moves.moved  # nothing left to do
