"""A day set by hand counts for late files, found folders, event folder (0618)."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.classify.event_folder import event_folder
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.found_folders import found_folders
from media_hygiene.classify.late_files import late_files
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.search.sidecar_days import read_days_again
from media_hygiene.tags.xmp_date import with_day

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_EASTER = ClassifyRule(
    name="Easter",
    match=RuleMatch.DATE_RANGE,
    category="Easter",
    dates="2024-03-30..2024-04-01",
)
_DAY = "2024-03-31"


@pytest.fixture(name="connection")
def connection_fixture() -> Iterator[sqlite3.Connection]:
    """An empty index, closed after the test."""
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE files (path TEXT, media_date TEXT, camera TEXT, full_digest TEXT)"
    )
    yield connection
    connection.close()


def _photo(connection: sqlite3.Connection, path: Path, digest: str) -> None:
    """An undated photo, indexed, whose sidecar holds the day.

    Args:
        connection: The index.
        path: The photo.
        digest: Its content id.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"jpeg")
    sidecar = path.with_suffix(".xmp")
    sidecar.write_bytes(cast("bytes", with_day(None, _DAY, "test")))
    connection.execute(
        "INSERT INTO files VALUES (?, NULL, NULL, ?)", (str(path), digest)
    )


def _late(connection: sqlite3.Connection) -> set[str]:
    """The content ids proposed to Easter, the sidecars read again first.

    Args:
        connection: The index.

    Returns:
        Them.
    """
    read_days_again(connection)
    found = late_files(connection, (_EASTER,), {})
    return {file.digest for event in found for file in event.files}


def test_a_hand_dated_photo_is_a_late_file(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    """Undated, its sidecar's day puts it in the event's days.

    Args:
        tmp_path: Where the photos lie.
        connection: The index.
    """
    assert not late_files(connection, (_EASTER,), {})  # a bare index: no table yet
    _photo(connection, tmp_path / "Stick" / "a.jpg", "h1")
    assert _late(connection) == {"h1"}


def test_moved_with_its_sidecar_it_still_counts(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    """The file and its sidecar moved together (the index follows the file).

    Args:
        tmp_path: Where the photos lie.
        connection: The index.
    """
    photo = tmp_path / "Stick" / "a.jpg"
    _photo(connection, photo, "h1")
    target = tmp_path / "Elsewhere"
    target.mkdir()
    photo.rename(target / "a.jpg")
    photo.with_suffix(".xmp").rename(target / "a.xmp")
    connection.execute("UPDATE files SET path = ?", (str(target / "a.jpg"),))
    assert _late(connection) == {"h1"}


def test_its_sidecar_moved_away_it_no_longer_counts(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    """The sidecar alone moved: the photo has no day, read at the next ask.

    Args:
        tmp_path: Where the photos lie.
        connection: The index.
    """
    photo = tmp_path / "Stick" / "a.jpg"
    _photo(connection, photo, "h1")
    assert _late(connection) == {"h1"}
    photo.with_suffix(".xmp").rename(tmp_path / "a.xmp")
    assert _late(connection) == set()


def test_its_own_date_wins_over_the_sidecar(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    """A file dated in May is no late file of Easter, whatever its sidecar says.

    Args:
        tmp_path: Where the photos lie.
        connection: The index.
    """
    _photo(connection, tmp_path / "Stick" / "a.jpg", "h1")
    connection.execute("UPDATE files SET media_date = '2024:05:01 10:00:00'")
    assert _late(connection) == set()


def test_a_hand_dated_photo_counts_in_a_found_folder_and_its_event(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    """Its day is a day of its event folder, which is found again by it.

    Args:
        tmp_path: Where the photos lie.
        connection: The index.
    """
    folder = tmp_path / "2024" / "2024-03" / "Easter"
    _photo(connection, folder / "a.jpg", "h1")
    read_days_again(connection)
    rules = FolderRules(generic=(), dates=())
    found = found_folders(connection, rules, 6.0)
    assert [(f.name, [d.isoformat() for d in f.days]) for f in found] == [
        ("Easter", [_DAY])
    ]
    assert event_folder(connection, _EASTER, "elsewhere") == str(folder)
