"""`import --since`: a file's day, the period, the last import's day (0476)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.actions.copy_in import CopyJob
from media_hygiene.errors import ConfigError
from media_hygiene.services import phone_period
from media_hygiene.services.import_period import within
from media_hygiene.services.import_plan import ImportPlan
from media_hygiene.services.import_since import (
    LAST_IMPORT_FILE,
    file_day,
    first_day,
    kept,
    last_import,
    name_day,
    today_local,
)
from media_hygiene.services.phone_plan import PhoneCase, PhoneFile, Verdict

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

TODAY = date(2026, 10, 29)


@pytest.mark.parametrize(
    ("name", "day"),
    [
        ("20261029_143000.jpg", TODAY),
        ("IMG_20261029_143000.jpg", TODAY),
        ("VID_20261029_143000.mp4", TODAY),
        ("PXL_20261029_143000123.jpg", TODAY),
        ("Screenshot_2026-10-29-14-30-00.png", TODAY),
        ("Screenshot_20261029-143000.png", TODAY),
        ("DSC00012.JPG", None),
        ("IMG_1234.HEIC", None),
        ("20261399_x.jpg", None),
        ("20260231_x.jpg", None),
    ],
)
def test_name_day(name: str, day: date | None) -> None:
    """Each pattern of a phone's names gives its day; none: no day."""
    assert name_day(name) == day


def test_file_day_falls_back_on_the_modified_time() -> None:
    """No day in the name: the modified time; nothing readable: None."""
    assert file_day("DSC1.JPG", "2026-10-01T10:00:00") == date(2026, 10, 1)
    assert file_day("DSC1.JPG", "2026-10-01T12:00:00Z") is not None
    assert file_day("IMG_20261029_1.jpg", "2020-01-01T00:00:00") == TODAY
    assert file_day("DSC1.JPG", "") is None


def test_first_day_of_each_period() -> None:
    """today, week (7 days), month, all, a day; None: the last import."""
    last = date(2026, 10, 20)
    assert first_day("today", TODAY, last) == TODAY
    assert first_day("Week", TODAY, last) == date(2026, 10, 23)
    assert first_day("month", TODAY, last) == date(2026, 10, 1)
    assert first_day("all", TODAY, last) is None
    assert first_day("2026-09-01", TODAY, last) == date(2026, 9, 1)
    assert first_day(None, TODAY, last) == last
    assert first_day(None, TODAY, None) is None
    with pytest.raises(ConfigError):
        first_day("yesterday", TODAY, None)


def test_kept_keeps_a_file_without_a_day() -> None:
    """An unknown day is imported: never lost."""
    assert kept("DSC1.JPG", "", TODAY)
    assert not kept("IMG_20261028_1.jpg", "", TODAY)
    assert kept("IMG_20261028_1.jpg", "", None)


def test_last_import_is_read_back(tmp_path: Path) -> None:
    """The day mh wrote (BOM, line end) is read back; none or junk: None."""
    assert last_import(tmp_path) is None
    (tmp_path / LAST_IMPORT_FILE).write_text("﻿2026-10-20\r\n", encoding="utf-8")
    assert last_import(tmp_path) == date(2026, 10, 20)
    (tmp_path / LAST_IMPORT_FILE).write_text("junk", encoding="utf-8")
    assert last_import(tmp_path) is None


@dataclass(frozen=True)
class _Locations:
    journal_dir: Path


@dataclass(frozen=True)
class _Runtime:
    locations: _Locations


def _verdict(name: str, case: PhoneCase) -> Verdict:
    return Verdict(PhoneFile(PurePosixPath("Camera") / name, 1, ""), case)


def test_phone_new_files_before_the_last_import_stay(tmp_path: Path) -> None:
    """Without --since: since the last import; a known file keeps its case."""
    day = today_local()
    (tmp_path / LAST_IMPORT_FILE).write_text(day.isoformat(), encoding="utf-8")
    old = f"IMG_{(day - timedelta(days=3)):%Y%m%d}_1.jpg"
    verdicts = (
        _verdict(f"IMG_{day:%Y%m%d}_1.jpg", PhoneCase.NEW),
        _verdict(old, PhoneCase.NEW),
        _verdict(old, PhoneCase.LIBRARY),
    )
    runtime = cast("Runtime", _Runtime(_Locations(tmp_path)))
    cases = [v.case for v in phone_period.held_back(runtime, verdicts, None)]
    assert cases == [PhoneCase.NEW, PhoneCase.OLDER, PhoneCase.LIBRARY]
    cases = [v.case for v in phone_period.held_back(runtime, verdicts, "all")]
    assert cases == [PhoneCase.NEW, PhoneCase.NEW, PhoneCase.LIBRARY]


def test_folder_since_week_copies_the_last_seven_days(tmp_path: Path) -> None:
    """A synthetic folder: only the files of the last 7 days are copied."""
    now = datetime.now(UTC)
    jobs = []
    for age in (0, 6, 8, 40):
        source = tmp_path / f"DSC{age:04}.JPG"
        source.write_bytes(b"x")
        stamp = (now - timedelta(days=age)).timestamp()
        os.utime(source, (stamp, stamp))
        jobs.append(CopyJob(source, tmp_path / "to" / source.name))
    plan = ImportPlan(tuple(jobs), ())
    week, older = within(plan, "week")
    assert [job.source.name for job in week.jobs] == ["DSC0000.JPG", "DSC0006.JPG"]
    assert older == 2
    assert within(plan, None) == (plan, 0)
