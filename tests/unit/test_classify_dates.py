"""The date of each file: EXIF, video tags in local time, names, folders, mtime."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from media_hygiene.classify.dates import clock_not_set, exif_date, name_date, video_date
from media_hygiene.classify.dating import DatingContext, dating_of, has_camera_trace
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.models import DateSource, MediaInput
from media_hygiene.config.classify_settings import NAME_DATES
from media_hygiene.plan.name_rules import compile_patterns
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import VisualFacts

ROOT = Path("/data/c/Photos")
BRUSSELS = ZoneInfo("Europe/Brussels")
RULES = FolderRules.build((), ((), ()))
MTIME = 1_500_000_000_000_000_000
CONTEXT = DatingContext(RULES, compile_patterns(NAME_DATES), BRUSSELS)


def photo(
    relative: str, taken_at: str | None = None, camera: str | None = None
) -> MediaInput:
    """A file of the library, with its EXIF date and camera."""
    visual = VisualFacts(0, 0, 1, 1, 0.0, taken_at, camera)
    return MediaInput(ROOT / relative, ROOT, 10, MTIME, visual)


def described(relative: str, metadata: MediaMetadata) -> MediaInput:
    """A file known by its metadata only (a video)."""
    return MediaInput(ROOT / relative, ROOT, 10, MTIME, metadata=metadata)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2019:06:12 14:30:12", datetime(2019, 6, 12, 14, 30, 12)),
        ("2019:06:12 14:30:12.345", datetime(2019, 6, 12, 14, 30, 12)),
        ("07/03/2002 20:55:38", datetime(2002, 3, 7, 20, 55, 38)),
        ("0000:00:00 00:00:00", None),
        ("garbage", None),
        (None, None),
    ],
)
def test_exif_dates_as_written(text: str | None, expected: datetime | None) -> None:
    """Standard, with sub-seconds, day first; zeros and garbage are no date."""
    assert exif_date(text) == expected


def test_a_utc_video_time_moves_to_the_right_year() -> None:
    """00:30 on 1 January in Brussels is 23:30 UTC on 31 December."""
    assert video_date("2023-12-31T23:30:00.000000Z", BRUSSELS) == datetime(
        2024, 1, 1, 0, 30
    )
    assert video_date("2024-01-01T00:30:00+0100", BRUSSELS) == datetime(
        2024, 1, 1, 0, 30
    )
    assert video_date("not a date", BRUSSELS) is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("IMG_20210712_101500", datetime(2021, 7, 12, 10, 15)),
        ("20171224_110305", datetime(2017, 12, 24, 11, 3, 5)),
        ("PXL_20230101_120000123", datetime(2023, 1, 1, 12)),
        ("IMG-20210712-WA0001", datetime(2021, 7, 12, 12)),
        ("2018-01-11_19h06_34", datetime(2018, 1, 11, 19, 6, 34)),
        ("Screenshot_20200301-101010", datetime(2020, 3, 1, 12)),
        ("Plage", None),
    ],
)
def test_dates_in_file_names(name: str, expected: datetime | None) -> None:
    """Phones, WhatsApp, screenshots and editors each write their own pattern."""
    assert name_date(name, CONTEXT.names) == expected


def test_the_chain_prefers_exif_then_video_name_folder_mtime() -> None:
    """The first reliable source wins; the mtime is last and not trusted."""
    exif = dating_of(photo("2019/a.jpg", taken_at="2019:06:12 14:30:12"), CONTEXT)
    video = dating_of(
        described("2019/b.mov", MediaMetadata(created="2019-06-12T10:00:00Z")),
        CONTEXT,
    )
    named = dating_of(photo("x/IMG_20210712_101500.jpg"), CONTEXT)
    folder = dating_of(photo("Juillet 2016/c.jpg"), CONTEXT)
    weak = dating_of(photo("x/c.jpg"), CONTEXT)
    assert [d.source for d in (exif, video, named, folder, weak)] == [
        DateSource.EXIF,
        DateSource.VIDEO,
        DateSource.NAME,
        DateSource.FOLDER,
        DateSource.MTIME,
    ]
    assert (folder.when.year, folder.when.month) == (2016, 7)
    assert weak.confidence == 0


def test_a_folder_that_contradicts_exif_makes_it_doubtful() -> None:
    """A `2016/Juillet 2016` photo dated 2011 goes to "to check"."""
    doubted = dating_of(
        photo("2016/Juillet 2016/a.jpg", taken_at="2011:01:01 10:00:00"), CONTEXT
    )
    assert doubted.source is DateSource.EXIF
    assert (
        doubted.confidence
        < dating_of(
            photo("2011/a.jpg", taken_at="2011:01:01 10:00:00"), CONTEXT
        ).confidence
    )


def test_a_camera_with_an_unset_clock_gives_way_to_its_folders() -> None:
    """Most of its shots disagree with their folders: the folders are believed."""
    stuck = [
        photo(f"{year}/{index}.jpg", taken_at="2010:01:01 10:00:00", camera="Stuck")
        for index, year in enumerate((2016, 2017, 2018))
    ]
    fine = photo("2010/ok.jpg", taken_at="2010:01:01 10:00:00", camera="Good")
    unset = clock_not_set([*stuck, fine], RULES)
    assert unset == {"Stuck"}
    context = DatingContext(RULES, CONTEXT.names, BRUSSELS, unset)
    assert dating_of(stuck[0], context).when.year == 2016


def test_undated_files_are_told_apart_by_a_camera_trace() -> None:
    """A device or a position says a camera took it; nothing says received."""
    assert has_camera_trace(photo("a.jpg", camera="Canon"))
    assert has_camera_trace(described("a.jpg", MediaMetadata(latitude=1, longitude=2)))
    assert not has_camera_trace(described("a.jpg", MediaMetadata()))
