"""`shrink` renames `.avi` → `.mp4`: albums and decisions follow, `undo` too (0418)."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

import pytest

from media_hygiene.report.burst_decisions import BurstDecision
from media_hygiene.report.decisions import (
    DecisionsFile,
    read_decisions,
    write_decisions,
)
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.share.albums import (
    ALBUMS_FILE,
    Album,
    AlbumEntry,
    AlbumsFile,
    read_albums,
    write_albums,
)
from tests.support.cli import run
from tests.support.runtime import make_runtime
from tests.support.shrink_clips import CAMERA, NEEDS_X264, audited

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

pytestmark = NEEDS_X264

_ADDED = dt.datetime(2026, 10, 29, 10, tzinfo=dt.UTC)


@pytest.fixture
def cli(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """The camera's clip audited."""
    return audited(locations, monkeypatch)


def _named(locations: Locations) -> set[str]:
    """The host paths `albums.json` and `decisions.json` name, read from the disk.

    Args:
        locations: Mount points.

    Returns:
        The paths.
    """
    reports = locations.reports_dir
    albums = read_albums(reports / ALBUMS_FILE)
    decisions = read_decisions(reports / DEFAULT_DECISIONS)
    return {
        *(entry.path for album in albums.albums for entry in album.entries),
        *(path for burst in decisions.bursts for path in burst.kept),
    }


def test_shrink_then_undo_rewrite_the_album_and_the_decisions(
    cli: CliRunner, locations: Locations
) -> None:
    """After shrink both name the `.mp4`; after undo the original again."""
    camera = locations.data_dir / CAMERA
    host = make_runtime(locations).mapper.to_host
    reports = locations.reports_dir
    reports.mkdir(parents=True, exist_ok=True)
    entry = AlbumEntry(
        path=host(camera), sha256="0" * 64, size=camera.stat().st_size, added=_ADDED
    )
    write_albums(
        reports / ALBUMS_FILE,
        AlbumsFile(albums=(Album(name="Holidays", entries=(entry,)),)),
    )
    write_decisions(
        reports / DEFAULT_DECISIONS,
        DecisionsFile(
            version=1,
            roots=(host(locations.data_dir),),
            bursts=(BurstDecision(kept=(host(camera),)),),
        ),
    )
    shrunk = run(cli, "shrink", "--apply", "--yes")
    assert shrunk.exit_code == 0, shrunk.output
    assert "Links updated" in " ".join(shrunk.output.split())
    assert _named(locations) == {host(camera.with_suffix(".mp4"))}
    undone = run(cli, "undo")
    assert undone.exit_code == 0, undone.output
    assert _named(locations) == {host(camera)}
