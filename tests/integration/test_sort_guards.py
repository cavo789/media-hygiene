"""`sort` refuses before anything moves: no journal, read-only, unsafe destinations."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from media_hygiene.errors import MountError, WorkbookError
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.sort import SortService
from media_hygiene.services.sort_inputs import find_workbook, load_inputs
from tests.support.runtime import make_locations, make_runtime
from tests.support.sorting import (
    EVENT_NAME,
    PARTY,
    build_library,
    classify,
    name_first_event,
    snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime


def prepare(runtime: Runtime) -> None:
    """Check readiness and prepare the sort of the latest workbook."""
    service = SortService(runtime, NullProgress())
    service.ensure_ready()
    service.prepare(load_inputs(runtime, find_workbook(runtime, None)))


def test_without_a_journal_nothing_moves(tmp_path: Path) -> None:
    """Without a journal, undo would be impossible."""
    locations = make_locations(tmp_path, MountKind.JOURNAL)
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    classify(runtime)
    with pytest.raises(MountError, match="No journal mount"):
        prepare(runtime)


def test_read_only_folders_are_refused(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Folders mounted `:ro`: the tip names `sort`."""
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    classify(runtime)
    monkeypatch.setattr("media_hygiene.services.acting.is_read_only", lambda _p: True)
    with pytest.raises(MountError) as raised:
        prepare(runtime)
    assert "'sort'" in (raised.value.tip or "")


def test_a_target_on_the_container_disk_is_refused(locations: Locations) -> None:
    """Files moved to a folder that is not mounted would vanish with the container."""
    build_library(locations.data_dir)
    mounted = locations.data_dir / PARTY
    runtime = make_runtime(locations)
    classify(runtime)
    runtime = replace(runtime, mounts=MountTable(frozenset({mounted})))
    with pytest.raises(MountError, match="not a mounted folder"):
        prepare(runtime)


def test_a_target_inside_a_protected_folder_is_refused(locations: Locations) -> None:
    """Protected folders are never changed: no file goes there either."""
    build_library(locations.data_dir)
    (locations.data_dir / "d").mkdir()
    target: Layer = {"classify": {"target": "D:\\Tri"}}
    classify(make_runtime(locations, target))
    protected: Layer = {"folders": {"protected": ["D:\\"]}}
    runtime = make_runtime(locations, target | protected)
    with pytest.raises(MountError, match="inside a protected folder"):
        prepare(runtime)


def test_a_destination_in_a_protected_folder_is_refused(locations: Locations) -> None:
    """The event named after a protected folder would write into it."""
    build_library(locations.data_dir)
    before = snapshot(locations.data_dir)
    runtime = make_runtime(
        locations, {"folders": {"protected": [f"C:\\2016\\{EVENT_NAME}"]}}
    )
    name_first_event(classify(runtime))
    with pytest.raises(WorkbookError, match="protected or excluded"):
        prepare(runtime)
    assert snapshot(locations.data_dir) == before


def test_a_path_too_long_for_windows_is_refused(locations: Locations) -> None:
    """Explorer cannot open it: the folder name must be shorter."""
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    name_first_event(classify(runtime), "/".join(["x" * 200, "y" * 100]))
    with pytest.raises(WorkbookError, match="longer than 259"):
        prepare(runtime)


def test_protected_files_stay_whatever_the_plan(locations: Locations) -> None:
    """A folder protected after `classify`: its files are counted, never moved."""
    build_library(locations.data_dir)
    name_first_event(classify(make_runtime(locations)))
    runtime = make_runtime(locations, {"folders": {"protected": ["C:\\Photos\\2016"]}})
    service = SortService(runtime, NullProgress())
    prepared = service.prepare(load_inputs(runtime, find_workbook(runtime, None)))
    assert prepared.plan.stay >= 6
    assert all(PARTY not in str(move.source) for move in prepared.plan.moves)
