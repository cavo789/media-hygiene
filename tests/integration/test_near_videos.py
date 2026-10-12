"""Re-encoded videos, from real files: listed, moved only with --tier near, undone."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.near_reviewing import open_near_review
from tests.support.cli import run
from tests.support.media import FFMPEG
from tests.support.near_videos import COPY, ORIGINAL, OTHER, write_near_videos
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

pytestmark = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg writes the videos")


@pytest.fixture
def videos(cli: CliRunner, locations: Locations) -> CliRunner:
    """The demo tree, plus a video, its smaller re-encoded copy and another video."""
    write_near_videos(locations.data_dir)
    return cli


def test_the_audit_lists_the_copy(videos: CliRunner, locations: Locations) -> None:
    """Counted in the summary, explained in a tip, shown in the report."""
    output = run(videos, "--verbosity", "verbose", "audit").output
    assert "Re-encoded videos (moved only with --tier near)" in output
    assert "Re-encoded videos are in the HTML report" in output
    report = next(locations.reports_dir.glob("*-audit/report.html")).read_text()
    assert "VID-20210714-WA0003.mp4" in report
    assert "Fractale.mp4" not in report
    page = next(locations.reports_dir.glob("*-audit/near.html")).read_text()
    assert '<a href="#near">' in page  # its own contents, burst series aside
    assert '<a href="#videos">' in page
    assert '<a href="#bursts">' not in page


def test_the_copy_moves_only_with_the_tier(
    videos: CliRunner, locations: Locations
) -> None:
    """A plain clean keeps it; --tier near-all quarantines it; undo brings it back."""
    data = locations.data_dir
    assert run(videos, "clean", "--yes").exit_code == 0
    assert (data / COPY).is_file()
    assert run(videos, "undo").exit_code == 0
    near = run(videos, "clean", "--yes", "--tier", "near-all")
    assert near.exit_code == 0, near.output
    assert not (data / COPY).exists()
    assert (data / ORIGINAL).is_file()
    assert (data / OTHER).is_file()
    assert run(videos, "undo").exit_code == 0
    assert (data / COPY).is_file()


@pytest.mark.usefixtures("videos")
def test_review_near_shows_a_video_without_preview(locations: Locations) -> None:
    """`review --near`: no preview for a video, played instead; length and codec."""
    runtime = make_runtime(locations)
    findings = AuditService(runtime, NullProgress()).run()
    target = locations.reports_dir / "decisions.json"
    groups = open_near_review(runtime, findings, target).state().groups
    [video] = [group for group in groups if group.kept.name == "Plage.mp4"]
    assert not video.kept.preview
    assert video.kept.original.endswith(".mp4")
    assert video.kept.video.startswith("/video/")
    assert "3 s" in video.kept.details
