"""`browse`: photos or videos only, and the orders of a list of files."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.search.folder_order import FileRow, is_shown, ordered


def test_videos_leave_out_photos_and_raw() -> None:
    """A `.jpg` and a `.cr2` are photos; an `.mp4` is a video."""
    names = ("a.jpg", "b.CR2", "c.mp4")
    assert [n for n in names if is_shown(Path(n), "videos")] == ["c.mp4"]
    assert [n for n in names if is_shown(Path(n), "photos")] == ["a.jpg", "b.CR2"]
    assert all(is_shown(Path(n), "all") for n in names)


def test_size_largest_first_ties_by_name() -> None:
    """Sorted on the bytes; equal sizes by name, whatever the case."""
    rows: list[FileRow] = [
        (1, "/d/b.jpg", 10, None),
        (2, "/d/A.jpg", 10, None),
        (3, "/d/c.jpg", 2_000, None),
        (4, "/d/d.jpg", 9, None),
    ]
    assert [row[0] for row in ordered(rows, "size")] == [3, 2, 1, 4]


def test_date_undated_last_and_name() -> None:
    """Oldest first, the undated at the end; by name otherwise."""
    rows: list[FileRow] = [
        (1, "/d/b.jpg", 1, None),
        (2, "/d/a.jpg", 1, "2020-01-02"),
        (3, "/d/c.jpg", 1, "2019-05-01"),
    ]
    assert [row[0] for row in ordered(rows, "date")] == [3, 2, 1]
    assert [row[0] for row in ordered(rows, "name")] == [2, 1, 3]
