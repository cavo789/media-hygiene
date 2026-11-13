"""0723: the show, TV, albums, storyteller and home page tag pictures from the index.

The tag is read from the index row (path, size, mtime), never stat-ed per tile. One test
per event that changes what a picture shows: the row the next audit (or the tool's own
move) writes gives another address, the address of the file on the disk now is kept for
good, the old one never.
"""

from __future__ import annotations

import os
import sqlite3
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from media_hygiene.index.schema import MOVE
from media_hygiene.report import preview_cache
from media_hygiene.review.versioned import disk_tag, index_tags, tagged
from media_hygiene.slideshow.notes import story_view
from media_hygiene.slideshow.pictures import picture_paths, thumb_path, tv_path
from media_hygiene.slideshow.slides import Film, Slide

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.slideshow.show import Show


def _photo(path: Path, colour: str = "red") -> Path:
    """Write a small JPEG."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 48), colour).save(path)
    return path


_OPEN: list[sqlite3.Connection] = []


@pytest.fixture(autouse=True)
def _closed() -> Iterator[None]:
    """Close the indexes a test opened."""
    yield
    while _OPEN:
        _OPEN.pop().close()


def _index(*paths: Path) -> sqlite3.Connection:
    """An index holding these files as audited now."""
    connection = sqlite3.connect(":memory:")
    _OPEN.append(connection)
    connection.execute("CREATE TABLE files (path TEXT UNIQUE, size INT, mtime_ns INT)")
    for path in paths:
        _audit(connection, path)
    return connection


def _audit(connection: sqlite3.Connection, path: Path) -> None:
    """Write the row an audit writes for a file."""
    now = path.stat()
    connection.execute(
        "INSERT INTO files VALUES (?, ?, ?) ON CONFLICT(path) DO UPDATE"
        " SET size = excluded.size, mtime_ns = excluded.mtime_ns",
        (str(path), now.st_size, now.st_mtime_ns),
    )


def _tag(connection: sqlite3.Connection) -> str:
    """The tag of the index's first file."""
    return index_tags(connection, [1]).get(1, "")


def _changed(connection: sqlite3.Connection, path: Path, before: str) -> None:
    """After an event and its audit: a new tag, the disk's, the old one never."""
    assert disk_tag(path) != before
    _audit(connection, path)
    after = index_tags(connection, [1])[1]
    assert after != before
    assert after == disk_tag(path)


def test_the_index_tag_is_the_disk_tag(tmp_path: Path) -> None:
    """A file as audited: its index tag is the one the server keeps for good."""
    source = _photo(tmp_path / "a.jpg")
    assert _tag(_index(source)) == disk_tag(source)


def test_an_edit_in_place_changes_the_tag(tmp_path: Path) -> None:
    """Edited in place (other size)."""
    source = _photo(tmp_path / "a.jpg")
    connection = _index(source)
    before = _tag(connection)
    with source.open("ab") as file:
        file.write(b"more")
    _changed(connection, source, before)


def test_a_same_time_other_size_changes_the_tag(tmp_path: Path) -> None:
    """Replaced keeping its time (a copy keeping the mtime), other size."""
    source = _photo(tmp_path / "a.jpg")
    connection = _index(source)
    before, kept = _tag(connection), source.stat().st_mtime_ns
    _photo(tmp_path / "b.jpg", "blue").replace(source)
    source.write_bytes(source.read_bytes() + b"x")
    os.utime(source, ns=(kept, kept))
    _changed(connection, source, before)


def test_an_atomic_save_changes_the_tag(tmp_path: Path) -> None:
    """Saved atomically: a new file renamed over it."""
    source = _photo(tmp_path / "a.jpg")
    connection = _index(source)
    before = _tag(connection)
    stat = source.stat()
    _photo(tmp_path / "new.jpg", "green").replace(source)
    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10**9))
    _changed(connection, source, before)


def test_a_touch_changes_the_tag(tmp_path: Path) -> None:
    """Touched: same bytes, another time."""
    source = _photo(tmp_path / "a.jpg")
    connection = _index(source)
    before = _tag(connection)
    stat = source.stat()
    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10**9))
    _changed(connection, source, before)


def test_a_move_by_the_tool_changes_the_tag(tmp_path: Path) -> None:
    """Moved by `sort` (or back by `undo`): the index row follows, so does the tag."""
    source = _photo(tmp_path / "a.jpg")
    connection = _index(source)
    before = _tag(connection)
    moved = tmp_path / "2024" / "a.jpg"
    moved.parent.mkdir()
    source.rename(moved)
    connection.execute(MOVE[0], (str(moved), str(source)))
    after = _tag(connection)
    assert after not in {before, ""}
    assert after == disk_tag(moved)
    assert disk_tag(source) == ""  # the old address is never kept for good


def test_a_preview_version_bump_changes_the_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A change in the way previews are made renames every picture."""
    source = _photo(tmp_path / "a.jpg")
    connection = _index(source)
    before = _tag(connection)
    monkeypatch.setattr(preview_cache, "_VERSION", 999)
    assert _tag(connection) not in {before, ""}


def test_a_file_gone_has_no_tag(tmp_path: Path) -> None:
    """A file no longer in the index, or an index that cannot be read: no tag."""
    source = _photo(tmp_path / "a.jpg")
    connection = _index(source)
    assert index_tags(connection, [2]) == {}
    connection.execute("DROP TABLE files")
    assert index_tags(connection, [1]) == {}
    assert tagged("/thumb/1.jpg", "") == "/thumb/1.jpg"


def test_the_show_and_album_addresses_carry_the_tag() -> None:
    """Slideshow, TV, album and storyteller addresses carry the slide's tag."""
    photo = Slide(3, tag="0f3a")
    assert thumb_path(3, "0f3a") == "/thumb/3.jpg?v=0f3a"
    assert tv_path(3, "0f3a") == "/tv/3.jpg?v=0f3a"
    assert picture_paths(photo) == {
        "key": 3,
        "thumb": "/thumb/3.jpg?v=0f3a",
        "photo": "/tv/3.jpg?v=0f3a",
    }
    film = picture_paths(Slide(4, film=Film(".mp4")))
    assert (film["thumb"], film["photo"]) == ("/thumb/4.jpg", "")  # a frame (0733)


class _Show:
    """The part of a show the storyteller reads."""

    def __init__(self, current: Slide, upcoming: Slide | None) -> None:
        self.current, self.upcoming = current, upcoming
        self.slides = (current,)
        self.position = 0


def test_the_storyteller_thumbs_carry_the_tag() -> None:
    """The storyteller's thumbnails carry the slides' tags."""
    show: Show = _Show(Slide(3, tag="aa"), Slide(4, tag="bb"))  # type: ignore[assignment]
    story = story_view(show)
    assert story["nowThumb"] == "thumb/3.jpg?v=aa"
    assert story["nextThumb"] == "thumb/4.jpg?v=bb"
