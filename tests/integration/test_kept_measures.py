"""Colours and same-stream digests are kept in the index: measured once per version."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene.constants import MediaKind
from media_hygiene.index.measures import Measure, MeasureStore
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan import colour
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.demo import build_demo
from tests.support.media import FFMPEG
from tests.support.near_videos import write_near_videos
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.plan.models import AuditFindings

KEPT = "c/Family Photos/2021/Plage.jpg"
_ONE_SECOND_NS = 1_000_000_000


@pytest.fixture
def opened(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """The demo tree; then every photo whose colour is measured, in order."""
    build_demo(locations.data_dir)
    real = colour.image_colour
    seen: list[Path] = []

    def counted(path: Path) -> float | None:
        seen.append(path)
        return real(path)

    monkeypatch.setattr(colour, "image_colour", counted)
    return seen


def audit(locations: Locations) -> AuditFindings:
    """Run an audit of the data mount point."""
    return AuditService(make_runtime(locations), NullProgress()).run()


def test_a_second_audit_opens_no_candidate(
    locations: Locations, opened: list[Path]
) -> None:
    """The first audit measures the candidates; the second reads them back."""
    first = audit(locations)
    assert opened, "the demo tree has near duplicates to measure"
    opened.clear()
    second = audit(locations)
    assert not opened
    assert second.similar.near == first.similar.near


def test_a_file_rewritten_in_place_is_measured_again(
    locations: Locations, opened: list[Path]
) -> None:
    """A new modification time: its stored colour no longer holds, the others do."""
    audit(locations)
    opened.clear()
    kept = locations.data_dir / KEPT
    # Saved by an editor: the file and its folder change (the listing of an unchanged
    # folder is reused, `services/listing`).
    for changed in (kept, kept.parent):
        stat = changed.stat()
        os.utime(changed, ns=(stat.st_atime_ns, stat.st_mtime_ns + _ONE_SECOND_NS))
    audit(locations)
    assert opened == [kept]


def test_the_store_holds_one_version_of_a_file() -> None:
    """Known for the very size and mtime only; a new version drops the old measures."""
    path = Path("/data/c/a.mp4")
    old = MediaFile(path, 10, 1, MediaKind.VIDEO)
    new = MediaFile(path, 11, 2, MediaKind.VIDEO)
    with FactsRepository.open(None) as index:
        store = MeasureStore(index.connection)
        store.keep([old], Measure.COLOUR, {path: 12.5})
        store.keep([old], Measure.STREAM, {path: "abc"})
        assert store.known([old], Measure.COLOUR, float) == {path: 12.5}
        assert store.known([old], Measure.STREAM, str) == {path: "abc"}
        assert not store.known([new], Measure.COLOUR, float)
        store.keep([new], Measure.COLOUR, {path: 3.0})
        assert store.known([new], Measure.COLOUR, float) == {path: 3.0}
        assert not store.known([new], Measure.STREAM, str)
        assert not store.known([old], Measure.COLOUR, float)


def test_a_file_left_out_is_not_stored() -> None:
    """A measure that could not be taken is tried again next time."""
    path = Path("/data/c/a.jpg")
    file = MediaFile(path, 10, 1, MediaKind.IMAGE)
    with FactsRepository.open(None) as index:
        store = MeasureStore(index.connection)
        store.keep([file], Measure.COLOUR, {})
        assert not store.known([file], Measure.COLOUR, float)


@pytest.mark.skipif(FFMPEG is None, reason="ffmpeg writes the videos")
def test_a_second_audit_runs_no_ffmpeg_for_colours(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Re-encoded videos are measured once."""
    write_near_videos(locations.data_dir)
    real = colour.video_colour
    seen: list[Path] = []

    async def counted(path: Path, duration: float, ffmpeg: str) -> float | None:
        seen.append(path)
        return await real(path, duration, ffmpeg)

    monkeypatch.setattr(colour, "video_colour", counted)
    first = audit(locations)
    assert seen, "the near videos are measured once"
    seen.clear()
    assert audit(locations).similar.videos == first.similar.videos
    assert not seen
