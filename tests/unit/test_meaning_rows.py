"""The vectors of search by meaning in the index: versions, moves, pruning, parking."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.meaning_rows import MeaningStore, vector_count, vectors
from media_hygiene.index.parked import park, unpark
from media_hygiene.index.repository import FactsRepository
from media_hygiene.meaning.clip import MODEL
from tests.support.meaning import colour_vector

_BLUE = colour_vector((60, 120, 230))
_WHITE = colour_vector((250, 250, 252))
_PHOTO = PhotoVersion(Path("/data/c/Photos/IMG_1.jpg"), 10, 7)
_OTHER = PhotoVersion(Path("/data/c/Photos/IMG_2.jpg"), 20, 7)


def _repository(tmp_path: Path) -> FactsRepository:
    """An index knowing both photos."""
    repository = FactsRepository.open(tmp_path / "index.sqlite")
    for photo in (_PHOTO, _OTHER):
        repository.connection.execute(
            "INSERT INTO files (path, size, mtime_ns) VALUES (?, ?, ?)",
            (str(photo.path), photo.size, photo.mtime_ns),
        )
    return repository


def test_a_vector_is_kept_for_one_version_and_one_model(tmp_path: Path) -> None:
    """Edited since (another size), the photo is missing again; another model too."""
    with _repository(tmp_path) as repository:
        store = MeaningStore(repository.connection, MODEL)
        assert store.missing((_PHOTO, _OTHER)) == (_PHOTO, _OTHER)
        assert store.seconds_per_photo() is None
        store.put(_PHOTO, _BLUE, 0.05)
        store.put(_OTHER, _WHITE, 0.0)  # a copy: no time of its own
        assert not store.missing((_PHOTO, _OTHER))
        edited = PhotoVersion(_PHOTO.path, 11, 7)
        assert store.missing((edited,)) == (edited,)
        assert MeaningStore(repository.connection, "other").missing((_PHOTO,))
        assert store.seconds_per_photo() == 0.05
        keys, matrix = vectors(repository.connection, MODEL)
        assert len(keys) == 2
        assert np.allclose(matrix[0], _BLUE)
        assert vector_count(repository.connection, MODEL) == 2
        assert vector_count(repository.connection, "other") == 0
        assert not vectors(repository.connection, "other")[0]


def test_a_stale_vector_is_never_read(tmp_path: Path) -> None:
    """The file changed since the vector: the search does not compare it."""
    with _repository(tmp_path) as repository:
        MeaningStore(repository.connection, MODEL).put(_PHOTO, _BLUE, 0.05)
        repository.connection.execute(
            "UPDATE files SET size = 99 WHERE path = ?", (str(_PHOTO.path),)
        )
        assert vector_count(repository.connection, MODEL) == 0


def test_an_index_older_than_the_table_has_no_vector(tmp_path: Path) -> None:
    """Read-only, an index of version 15 is not upgraded: nothing to compare."""
    with closing(sqlite3.connect(tmp_path / "old.sqlite")) as connection:
        assert vector_count(connection, MODEL) == 0
        keys, matrix = vectors(connection, MODEL)
        assert not keys
        assert matrix.shape == (0, 0)


def test_the_vector_follows_a_move_and_goes_with_a_forgotten_file(
    tmp_path: Path,
) -> None:
    """`sort` or the audit move the photo: its vector follows; gone, it goes."""
    moved = "/data/c/Photos/2024/IMG_1.jpg"
    with _repository(tmp_path) as repository:
        store = MeaningStore(repository.connection, MODEL)
        store.put(_PHOTO, _BLUE, 0.05)
        store.put(_OTHER, _WHITE, 0.05)
        repository.move([(str(_PHOTO.path), moved)])
        assert not store.missing((PhotoVersion(Path(moved), 10, 7),))
        repository.forget([str(_OTHER.path)])
        assert store.missing((_OTHER,)) == (_OTHER,)
        assert vector_count(repository.connection, MODEL) == 1


def test_a_clean_parks_the_vector_and_undo_puts_it_back(tmp_path: Path) -> None:
    """Set aside, the photo leaves the table; restored, it has its vector again."""
    quarantined = "/quarantine/run/IMG_1.jpg"
    with _repository(tmp_path) as repository:
        connection = repository.connection
        store = MeaningStore(connection, MODEL)
        store.put(_PHOTO, _BLUE, 0.05)
        park(connection, "run", [(str(_PHOTO.path), quarantined)])
        assert store.missing((_PHOTO,)) == (_PHOTO,)
        assert unpark(connection, [(quarantined, str(_PHOTO.path))]) == 1
        assert not store.missing((_PHOTO,))
        keys, matrix = vectors(connection, MODEL)
        assert len(keys) == 1
        assert np.allclose(matrix[0], _BLUE)
