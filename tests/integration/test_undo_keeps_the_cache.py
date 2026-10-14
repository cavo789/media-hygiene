"""`undo` of a clean gets back what the cache knew; `purge` forgets it (TODO 0156)."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.cli.cmd_purge import _purge
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanMode, CleanService
from media_hygiene.services.undo import undo_run
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_PARKED = "SELECT COUNT(*) FROM parked"


def clean(runtime: Runtime) -> str:
    """Audit then clean to the quarantine; return the run identifier."""
    findings = AuditService(runtime, NullProgress()).run()
    service = CleanService(runtime, NullProgress())
    service.ensure_ready(CleanMode())
    run_id, _outcome = service.execute(service.feasible(replace(findings.plan)))
    return run_id


def parked(locations: Locations) -> int:
    """How many files the index keeps aside."""
    with FactsRepository.open(locations.index_file) as repository:
        return int(repository.connection.execute(_PARKED).fetchone()[0])


def test_restored_files_are_not_checked_again(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Clean parks the rows of the copies set aside; undo puts them back."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    assert parked(locations)
    undo_run(runtime, run_id, NullProgress())
    assert not parked(locations)

    def forbidden(*_args: object) -> None:
        raise AssertionError

    for name in ("inspect_image", "read_image_metadata", "inspect_raw", "probe_video"):
        monkeypatch.setattr(f"media_hygiene.scan.file_check.{name}", forbidden)
    AuditService(runtime, NullProgress()).run()


def test_purge_forgets_the_parked_rows(locations: Locations) -> None:
    """Once the quarantine of a run is erased, its rows are gone too."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    assert parked(locations)
    _purge(runtime, [run_id])
    assert not parked(locations)
