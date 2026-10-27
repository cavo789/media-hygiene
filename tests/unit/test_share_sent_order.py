"""0370: an album's copies numbered by the moment taken: a sort by name follows."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import TYPE_CHECKING

from media_hygiene.share.sent_order import numbered_stems

if TYPE_CHECKING:
    from pathlib import Path


def _file(folder: Path, name: str, when: datetime) -> Path:
    """A file dated `when` (local time)."""
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    os.utime(path, (when.timestamp(), when.timestamp()))
    return path


def _index(path: Path, taken: dict[Path, str]) -> Path:
    """An index holding the EXIF date of some files."""
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE files (path TEXT, taken_at TEXT)")
        connection.executemany(
            "INSERT INTO files VALUES (?, ?)", [(str(k), v) for k, v in taken.items()]
        )
        connection.commit()
    return path


def test_two_cameras_mixed_come_out_in_the_order_taken(tmp_path: Path) -> None:
    """The EXIF date wins over the name and the folder; the day names the copy."""
    copied = datetime(2024, 1, 1, 12)  # noqa: DTZ001 - a file's local date
    late = _file(tmp_path / "a", "AAA.jpg", copied)
    early = _file(tmp_path / "b", "ZZZ.jpg", copied)
    index = _index(
        tmp_path / "index.sqlite",
        {late: "2023:07:12 09:00:00", early: "2023:07:10 18:30:00"},
    )
    assert numbered_stems(index, [late, early]) == [
        (early, "001_2023-07-10"),
        (late, "002_2023-07-12"),
    ]


def test_without_a_date_the_files_date_then_the_name(tmp_path: Path) -> None:
    """No index: the file's date orders; the same moment, the name."""
    day = datetime(2023, 7, 10, 12)  # noqa: DTZ001 - a file's local date
    b = _file(tmp_path, "b.jpg", day)
    a = _file(tmp_path, "a.jpg", day)
    first = _file(tmp_path, "z.jpg", datetime(2023, 7, 9, 12))  # noqa: DTZ001
    assert [stem for _p, stem in numbered_stems(None, [b, a, first])] == [
        "001_2023-07-09",
        "002_2023-07-10",
        "003_2023-07-10",
    ]
    assert [p for p, _stem in numbered_stems(None, [b, a, first])] == [first, a, b]


def test_a_thousand_photos_take_four_digits(tmp_path: Path) -> None:
    """The width follows the count: 1,000 photos, `0001` … `1000`."""
    day = datetime(2023, 7, 10, 12)  # noqa: DTZ001 - a file's local date
    photos = [_file(tmp_path, f"{n}.jpg", day) for n in range(1000)]
    stems = [stem for _p, stem in numbered_stems(None, photos)]
    assert stems[0] == "0001_2023-07-10"
    assert stems[-1] == "1000_2023-07-10"
