"""`undo` checks what an undo needs, not what `clean` needs (0052)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.undo import undo_run
from media_hygiene.services.undo_guard import ensure_undo_ready, quarantined_count
from tests.integration.test_clean_undo import clean, manifest
from tests.integration.test_undo_sort import SortRun
from tests.integration.test_undo_sort_runs import answer_yes, sorted_twice
from tests.support.cli import run
from tests.support.demo import build_demo
from tests.support.runtime import make_locations, make_runtime
from tests.support.sorting import snapshot

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations

QUARANTINE_ENV = "MEDIA_HYGIENE_QUARANTINE_DIR"
OTHER_FILES: Layer = {"scan": {"extensions": ["pdf", "jpg"]}}


def without_quarantine(monkeypatch: pytest.MonkeyPatch) -> None:
    """The command line runs with no `/quarantine` mounted, other files asked for.

    Asking for other files than media (`pdf`) makes `clean` require the quarantine.
    """
    monkeypatch.delenv(QUARANTINE_ENV)
    monkeypatch.setenv("MEDIA_HYGIENE_SCAN__EXTENSIONS", '["pdf", "jpg"]')


def test_read_only_folders_name_undo(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The undo of a sort run on `:ro` folders: refused, the tip names `undo`."""
    sort_run = SortRun(locations.data_dir / "photos", locations.journal_dir)
    monkeypatch.setattr("media_hygiene.services.acting.is_read_only", lambda _p: True)
    result = run(cli, "undo", "--yes")
    assert result.exit_code != 0
    assert "'undo'" in result.output
    assert "'clean'" not in result.output
    assert not sort_run.source.exists()


def test_a_sort_run_needs_no_quarantine(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Other files asked for, no `/quarantine`: the sort run is undone all the same."""
    sort_run = SortRun(locations.data_dir / "photos", locations.journal_dir)
    without_quarantine(monkeypatch)
    result = run(cli, "undo", "--yes")
    assert result.exit_code == 0, result.output
    for name, data in sort_run.photos.items():
        assert (sort_run.source / name).read_bytes() == data


def test_quarantined_files_need_the_quarantine(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A clean run that quarantined files, `/quarantine` not mounted: nothing moves."""
    run_id = clean(make_runtime(locations))
    before = manifest(locations.data_dir)
    without_quarantine(monkeypatch)
    result = run(cli, "undo")
    assert result.exit_code != 0
    assert run_id in result.output
    assert "/quarantine" in result.output
    assert "Mount the same quarantine folder" in result.output
    assert manifest(locations.data_dir) == before


def test_deletions_alone_are_undone_without_quarantine(tmp_path: Path) -> None:
    """A `clean --delete` without quarantine rebuilds its copies from the kept ones."""
    locations = make_locations(tmp_path, MountKind.QUARANTINE)
    build_demo(locations.data_dir)
    before = manifest(locations.data_dir)
    run_id = clean(make_runtime(locations), delete=True)
    assert manifest(locations.data_dir) != before
    runtime = make_runtime(locations, OTHER_FILES)
    assert runtime.settings.scan.other_files
    assert quarantined_count(runtime, run_id) == 0
    ensure_undo_ready(runtime, [run_id])
    outcome = undo_run(runtime, run_id, NullProgress())
    assert not outcome.failed
    assert set(manifest(locations.data_dir)) == set(before)


def test_an_undone_quarantine_is_needed_no_more(locations: Locations) -> None:
    """Once its files are back, a run no longer waits for the quarantine."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    assert quarantined_count(runtime, run_id) > 0
    undo_run(runtime, run_id, NullProgress())
    assert quarantined_count(runtime, run_id) == 0


def test_a_grouped_sort_with_quarantined_junk_is_refused(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each run of the sort is checked: no question asked, nothing moved back."""
    _runtime, _before = sorted_twice(locations)
    after = snapshot(locations.data_dir)
    asked = answer_yes(monkeypatch)
    monkeypatch.delenv(QUARANTINE_ENV)
    result = run(cli, "undo")
    assert result.exit_code != 0
    assert "Mount the same quarantine folder" in result.output  # Thumbs.db
    assert not asked
    assert snapshot(locations.data_dir) == after
