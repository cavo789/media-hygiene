"""Folders a sort empties: junk to the quarantine, folder removed, undo restores."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.sort import SortService
from media_hygiene.services.sort_inputs import find_workbook, load_inputs
from tests.support.runtime import make_locations, make_runtime
from tests.support.sorting import (
    MIXED,
    PARTY,
    WEDDING,
    build_library,
    classify,
    name_first_event,
    sort,
    undo,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations


def test_junk_is_quarantined_and_undo_restores_it(locations: Locations) -> None:
    """Thumbs.db and desktop.ini go to the run's quarantine, then come back."""
    data = locations.data_dir
    build_library(data)
    thumbs = (data / PARTY / "Thumbs.db").read_bytes()
    runtime = make_runtime(locations)
    name_first_event(classify(runtime))
    result = sort(runtime)
    quarantine = locations.quarantine_dir / result.run_id
    assert sorted(path.name for path in quarantine.rglob("*") if path.is_file()) == [
        "Thumbs.db",
        "desktop.ini",
    ]
    assert result.moves.outcome.quarantined == 2
    assert [v.folder.name for v in result.folders.kept] == ["Divers"]
    undo(runtime, result.run_id)
    assert (data / PARTY / "Thumbs.db").read_bytes() == thumbs
    assert (data / WEDDING / "desktop.ini").is_file()
    assert not any(path.is_file() for path in quarantine.rglob("*"))


def test_the_prediction_matches_what_is_done(locations: Locations) -> None:
    """The summary before the confirmation says which folders will go."""
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    name_first_event(classify(runtime))
    service = SortService(runtime, NullProgress())
    prepared = service.prepare(load_inputs(runtime, find_workbook(runtime, None)))
    result = service.execute(prepared, lambda: False)
    assert prepared.folders == result.folders


def test_keep_empty_folders_removes_nothing(locations: Locations) -> None:
    """`--keep-empty-folders`: the emptied folders and their junk stay."""
    data = locations.data_dir
    build_library(data)
    runtime = make_runtime(locations)
    name_first_event(classify(runtime))
    service = SortService(runtime, NullProgress())
    inputs = load_inputs(runtime, find_workbook(runtime, None))
    prepared = service.prepare(inputs, keep_empty=True)
    assert prepared.folders.removed == 0
    result = service.execute(prepared, lambda: False)
    assert (data / PARTY / "Thumbs.db").is_file()
    assert result.folders.removed == 0


def test_without_a_quarantine_a_folder_with_junk_stays(tmp_path: Path) -> None:
    """No quarantine mount: the junk has nowhere to go, its folder stays."""
    locations = make_locations(tmp_path, MountKind.QUARANTINE)
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    name_first_event(classify(runtime))
    result = sort(runtime)
    assert (locations.data_dir / PARTY / "Thumbs.db").is_file()
    kept = {verdict.folder.name for verdict in result.folders.kept}
    assert {"Juillet 2016", "Mariage", "Divers"} <= kept
    assert (locations.data_dir / MIXED / "notes.txt").is_file()
