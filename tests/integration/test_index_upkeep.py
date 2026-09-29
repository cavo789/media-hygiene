"""The index follows the disk: files gone are forgotten, metadata is filled once."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.image_check import read_image_metadata
from media_hygiene.scan.metadata import METADATA_VERSION
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanService
from media_hygiene.services.undo import resolve_run_id, undo_run
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

CHECKS = "media_hygiene.scan.file_check"

if TYPE_CHECKING:
    import pytest

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime


def audit(locations: Locations, cli: Layer | None = None) -> AuditFindings:
    """Run an audit with the persistent test index."""
    return AuditService(make_runtime(locations, cli), NullProgress()).run()


def indexed(locations: Locations) -> set[str]:
    """Every path the index holds a row for."""
    with FactsRepository.open(locations.index_file) as repository:
        return set(repository.paths_under(locations.data_dir))


def media_on_disk(locations: Locations) -> set[str]:
    """Every photo and video of the data folder (no sidecar, no text file)."""
    return {
        str(path)
        for path in locations.data_dir.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".jpg", ".png", ".mp4"}
    }


def test_deleted_and_renamed_files(locations: Locations) -> None:
    """A deleted file loses its row; a renamed one keeps one row, under its new name."""
    build_demo(locations.data_dir)
    audit(locations)
    deleted, renamed = sorted(media_on_disk(locations))[:2]
    Path(deleted).unlink()
    new_name = Path(renamed).with_name("renamed by hand.jpg")
    Path(renamed).rename(new_name)
    audit(locations)
    rows = indexed(locations)
    assert deleted not in rows
    assert renamed not in rows
    assert str(new_name) in rows


def test_an_audit_limited_by_ext_forgets_nothing_else(locations: Locations) -> None:
    """`--ext png` does not look at the photos: their rows stay."""
    build_demo(locations.data_dir)
    audit(locations)
    before = indexed(locations)
    audit(locations, {"scan": {"extensions": ["png"]}})
    assert indexed(locations) == before


def clean(runtime: Runtime) -> None:
    """Audit then clean."""
    findings = AuditService(runtime, NullProgress()).run()
    service = CleanService(runtime, NullProgress())
    service.ensure_ready()
    service.execute(service.feasible(findings.plan))


def test_clean_forgets_what_it_removed_and_undo_brings_it_back(
    locations: Locations,
) -> None:
    """After clean, no row points to a missing file; after undo, audits see them."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    before = media_on_disk(locations)
    clean(runtime)
    removed = before - media_on_disk(locations)
    assert removed
    assert not removed & indexed(locations)
    undo_run(runtime, resolve_run_id(runtime, None), NullProgress())
    audit(locations)
    # Empty files are never indexed: there is nothing to hash or decode.
    restored = {path for path in removed if Path(path).stat().st_size}
    assert restored <= indexed(locations)


def test_older_entries_get_their_metadata_once_without_decoding(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An index of 0.2 (no metadata): readable images get a header read only."""
    build_demo(locations.data_dir)
    first = audit(locations)
    with closing(sqlite3.connect(locations.index_file)) as connection:
        read = connection.execute(
            "SELECT path FROM files"
            " WHERE metadata_version > 0 AND broken_reason IS NULL"
        )
        images = [row[0] for row in read if media_kind(Path(row[0])) is MediaKind.IMAGE]
        connection.execute("UPDATE files SET metadata_version = 0, metadata = NULL")
        connection.commit()
    headers: list[Path] = []

    def counting_header(path: Path) -> object:
        headers.append(path)
        return read_image_metadata(path)

    def forbidden(*_args: object) -> None:
        raise AssertionError

    monkeypatch.setattr(f"{CHECKS}.read_image_metadata", counting_header)
    monkeypatch.setattr(f"{CHECKS}.inspect_image", forbidden)
    second = audit(locations)
    assert sorted(map(str, headers)) == sorted(images)
    assert second.inventory.dated_images == first.inventory.dated_images
    assert second.inventory.formats == first.inventory.formats
    with closing(sqlite3.connect(locations.index_file)) as connection:
        versions = connection.execute(
            "SELECT DISTINCT metadata_version FROM files WHERE metadata IS NOT NULL"
        ).fetchall()
    assert versions == [(METADATA_VERSION,)]
