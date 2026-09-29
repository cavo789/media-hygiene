"""The SQLite index of facts."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Final

from media_hygiene.constants import BrokenReason, MediaKind
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.schema import SCHEMA_VERSION
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import MediaFile, VisualFacts

VERSION_1_TABLE: Final = (
    "CREATE TABLE files (path TEXT PRIMARY KEY, size INTEGER NOT NULL,"
    " mtime_ns INTEGER NOT NULL, partial_digest TEXT, full_digest TEXT,"
    " integrity_checked INTEGER NOT NULL DEFAULT 0, broken_reason TEXT,"
    " broken_detail TEXT NOT NULL DEFAULT '')"
)


def test_facts_round_trip_and_invalidation(tmp_path: Path) -> None:
    """Facts survive a reopen, and a new mtime makes them stale."""
    index = tmp_path / "index.sqlite"
    file = MediaFile(tmp_path / "a.jpg", 10, 1, MediaKind.IMAGE)
    facts = (
        FileFacts()
        .with_partial("p")
        .with_full("f")
        .with_integrity(BrokenReason.UNREADABLE_IMAGE, "boom")
    )
    with FactsRepository.open(index) as repository:
        repository.put(file, facts)
    with FactsRepository.open(index) as repository:
        assert repository.get(file) == facts
        touched = MediaFile(file.path, file.size, 2, file.kind)
        assert repository.get(touched) == FileFacts()


def test_in_memory_index_starts_empty(tmp_path: Path) -> None:
    """Without a cache mount the index lives in memory only."""
    file = MediaFile(tmp_path / "a.jpg", 10, 1, MediaKind.IMAGE)
    with FactsRepository.open(None) as repository:
        assert repository.get(file) == FileFacts()
        repository.put(file, FileFacts().with_integrity(None, ""))
        assert repository.get(file).integrity_checked


def test_visual_facts_round_trip(tmp_path: Path) -> None:
    """64-bit hashes (above SQLite's signed range too) and EXIF details survive."""
    index = tmp_path / "index.sqlite"
    file = MediaFile(tmp_path / "a.jpg", 10, 1, MediaKind.IMAGE)
    visual = VisualFacts(
        2**64 - 1, 5, 4000, 3000, 123.4, "2021:07:04 10:15:00", "Canon"
    )
    facts = FileFacts().with_visual(visual).with_integrity(None, "")
    with FactsRepository.open(index) as repository:
        repository.put(file, facts)
    with FactsRepository.open(index) as repository:
        assert repository.get(file) == facts


def test_an_index_of_version_1_is_upgraded(tmp_path: Path) -> None:
    """Digests are kept; images must be described once (visual_checked is false)."""
    index = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        connection.execute(VERSION_1_TABLE)
        connection.execute(
            "INSERT INTO files VALUES ('/data/a.jpg', 10, 1, 'p', 'f', 1, NULL, '')"
        )
        connection.commit()
    file = MediaFile(Path("/data/a.jpg"), 10, 1, MediaKind.IMAGE)
    with FactsRepository.open(index) as repository:
        facts = repository.get(file)
    assert (facts.full_digest, facts.integrity_checked) == ("f", True)
    assert not facts.visual_checked
    with closing(sqlite3.connect(index)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (SCHEMA_VERSION,)


def test_metadata_round_trip_and_typed_columns(tmp_path: Path) -> None:
    """The JSON comes back whole; place and date are copied where queries find them."""
    index = tmp_path / "index.sqlite"
    photo = MediaFile(tmp_path / "a.jpg", 10, 1, MediaKind.IMAGE)
    video = MediaFile(tmp_path / "b.mov", 20, 1, MediaKind.VIDEO)
    visual = VisualFacts(1, 2, 40, 30, 1.0, "2021:07:04 10:15:00")
    place = MediaMetadata(latitude=48.85, longitude=2.35, rating=5)
    recorded = MediaMetadata(created_local="2024-01-01T00:30:00+0100", duration=3.5)
    facts = {
        photo: FileFacts().with_visual(visual).with_metadata(place),
        video: FileFacts().with_metadata(recorded),
    }
    with FactsRepository.open(index) as repository:
        for file, their_facts in facts.items():
            repository.put(file, their_facts.with_integrity(None, ""))
    with FactsRepository.open(index) as repository:
        assert repository.get(photo).metadata == place
        assert repository.get(video).metadata == recorded
    with closing(sqlite3.connect(index)) as connection:
        rows = connection.execute(
            "SELECT latitude, longitude, media_date FROM files ORDER BY path"
        ).fetchall()
    assert rows == [
        (48.85, 2.35, "2021:07:04 10:15:00"),
        (None, None, "2024-01-01T00:30:00+0100"),
    ]


def test_unreadable_metadata_is_read_again(tmp_path: Path) -> None:
    """A corrupt JSON reads as never read: the next audit fills it again."""
    index = tmp_path / "index.sqlite"
    file = MediaFile(tmp_path / "a.jpg", 10, 1, MediaKind.IMAGE)
    with FactsRepository.open(index) as repository:
        repository.put(file, FileFacts().with_metadata(MediaMetadata(rating=3)))
    with closing(sqlite3.connect(index)) as connection:
        connection.execute("UPDATE files SET metadata = '{not json'")
        connection.commit()
    with FactsRepository.open(index) as repository:
        facts = repository.get(file)
    assert (facts.metadata, facts.metadata_version) == (None, 0)
    with FactsRepository.open(index) as repository:
        repository.put(file, FileFacts().with_metadata(None))
        assert repository.get(file).metadata_version > 0  # nothing to say: not re-read
