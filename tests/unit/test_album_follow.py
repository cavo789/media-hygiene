"""Albums follow their files (0295): every way a file leaves its path, one test each.

The tool's own moves (`sort`, recorded by the index; the quarantine, then `undo`), the
user's (a folder renamed in the Explorer, seen by the next audit), a file deleted;
identical copies settled by name, then path. Each change read back from the disk.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.schema import prepare
from media_hygiene.services.albums import album_store
from media_hygiene.share.album_store import AlbumChange
from media_hygiene.share.albums import ALBUMS_FILE
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_store import AlbumStore

_ALBUM: Final = "Crete 2023"
_PHOTO: Final = "c/Photos/2023 Crete/IMG_1.jpg"
_HOST: Final = "C:\\Photos\\2023 Crete\\IMG_1.jpg"


@pytest.fixture
def runtime(tmp_path: Path) -> Runtime:
    """A runtime whose folders lie under the test's folder, with an empty index."""
    runtime = make_runtime(make_locations(tmp_path))
    with closing(sqlite3.connect(runtime.locations.index_file)) as connection:
        prepare(connection)
        connection.commit()
    return runtime


def _write(runtime: Runtime, relative: str, content: bytes = b"crete") -> Path:
    """A file under the data folder, known to the index (no full digest, as usual)."""
    path = runtime.locations.data_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    _index_row(runtime, path)
    return path


def _index_row(runtime: Runtime, path: Path, digest: str | None = None) -> None:
    """What an audit stores of a file: its path, size, modification time."""
    stat = path.stat()
    with closing(sqlite3.connect(runtime.locations.index_file)) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO files (path, size, mtime_ns, full_digest)"
            " VALUES (?, ?, ?, ?)",
            (str(path), stat.st_size, stat.st_mtime_ns, digest),
        )
        connection.commit()


def _forget(runtime: Runtime, path: Path) -> None:
    """What an audit (or `clean`) does once a file is gone: its row goes."""
    with closing(sqlite3.connect(runtime.locations.index_file)) as connection:
        connection.execute("DELETE FROM files WHERE path = ?", (str(path),))
        connection.commit()


def _album(runtime: Runtime, *files: Path) -> AlbumStore:
    store = album_store(runtime)
    store.add(AlbumChange(_ALBUM, files))
    return store


def _on_disk(runtime: Runtime) -> list[str]:
    """The paths of the album, read from `albums.json` itself."""
    saved = json.loads((runtime.locations.reports_dir / ALBUMS_FILE).read_text())
    return [entry["path"] for entry in saved["albums"][0]["entries"]]


def test_a_file_still_there_is_kept_as_it_is(runtime: Runtime) -> None:
    """Its digest computed once, at the add; nothing missing."""
    photo = _write(runtime, _PHOTO)
    shelf = _album(runtime, photo).on_disk()
    (entry,) = shelf.albums.albums[0].entries
    assert entry.path == _HOST
    assert entry.sha256 == hashlib.sha256(b"crete").hexdigest()
    assert shelf.missing[_ALBUM] == ()


def test_the_index_digest_is_used_when_it_knows_this_version(
    runtime: Runtime,
) -> None:
    """A file the audit fully hashed is not read again."""
    photo = _write(runtime, _PHOTO)
    _index_row(runtime, photo, "a" * 64)
    shelf = _album(runtime, photo).on_disk()
    assert shelf.albums.albums[0].entries[0].sha256 == "a" * 64


def test_a_folder_renamed_in_the_explorer_is_found_after_the_audit(
    runtime: Runtime,
) -> None:
    """Missing until an audit sees the new folder, then followed and saved."""
    photo = _write(runtime, _PHOTO)
    store = _album(runtime, photo)
    renamed = runtime.locations.data_dir / "c/Photos/Crete holidays"
    photo.parent.rename(renamed)
    assert store.on_disk().missing[_ALBUM] == (_HOST,)
    _forget(runtime, photo)
    _index_row(runtime, renamed / "IMG_1.jpg")
    shelf = store.on_disk()
    assert shelf.missing[_ALBUM] == ()
    assert _on_disk(runtime) == ["C:\\Photos\\Crete holidays\\IMG_1.jpg"]


def test_a_file_moved_by_sort_is_followed_through_the_index_moves(
    runtime: Runtime,
) -> None:
    """`sort` moves the file and its index row, and records the move."""
    photo = _write(runtime, _PHOTO)
    store = _album(runtime, photo)
    sorted_to = runtime.locations.data_dir / "c/Photos/2023/2023-07 Crete/IMG_1.jpg"
    sorted_to.parent.mkdir(parents=True)
    photo.rename(sorted_to)
    with FactsRepository.open(runtime.locations.index_file) as repository:
        repository.move([(str(photo), str(sorted_to))])
    assert store.on_disk().missing[_ALBUM] == ()
    assert _on_disk(runtime) == ["C:\\Photos\\2023\\2023-07 Crete\\IMG_1.jpg"]


def test_a_file_in_quarantine_is_missing_then_back_after_undo(
    runtime: Runtime,
) -> None:
    """Never dropped: the entry waits, and is there again once the file is back."""
    photo = _write(runtime, _PHOTO)
    store = _album(runtime, photo)
    quarantined = runtime.locations.quarantine_dir / "run" / photo.name
    quarantined.parent.mkdir(parents=True)
    photo.rename(quarantined)
    _forget(runtime, photo)
    assert store.on_disk().missing[_ALBUM] == (_HOST,)
    assert _on_disk(runtime) == [_HOST]
    quarantined.rename(photo)  # `undo`
    assert store.on_disk().missing[_ALBUM] == ()
    assert _on_disk(runtime) == [_HOST]


def test_a_deleted_file_is_said_missing_and_kept(runtime: Runtime) -> None:
    """No copy anywhere: missing on every read, never dropped silently."""
    photo = _write(runtime, _PHOTO)
    other = _write(runtime, "c/Photos/2023 Crete/IMG_2.jpg", b"other")
    store = _album(runtime, photo, other)
    photo.unlink()
    _forget(runtime, photo)
    for _read in range(2):
        assert store.on_disk().missing[_ALBUM] == (_HOST,)
    assert len(_on_disk(runtime)) == 2


def test_identical_copies_the_one_of_the_same_name_then_the_first_path(
    runtime: Runtime,
) -> None:
    """`clean` removed the album's copy: the same name wins, then the first path."""
    photo = _write(runtime, _PHOTO)
    store = _album(runtime, photo)
    _write(runtime, "c/Backup/a/other name.jpg")
    _write(runtime, "c/Backup/z/IMG_1.jpg")
    _write(runtime, "c/Backup/y/IMG_1.jpg")
    photo.unlink()
    _forget(runtime, photo)
    store.on_disk()
    assert _on_disk(runtime) == ["C:\\Backup\\y\\IMG_1.jpg"]


def test_a_copy_found_again_already_in_the_album_is_kept_once(
    runtime: Runtime,
) -> None:
    """Both copies were added; one removed: the album keeps the other, once."""
    photo = _write(runtime, _PHOTO)
    copy = _write(runtime, "c/Backup/IMG_1.jpg")
    store = _album(runtime, photo, copy)
    photo.unlink()
    _forget(runtime, photo)
    shelf = store.on_disk()
    assert shelf.missing[_ALBUM] == ()
    assert _on_disk(runtime) == ["C:\\Backup\\IMG_1.jpg"]


def test_without_an_index_a_moved_file_is_missing(runtime: Runtime) -> None:
    """The cache deleted: nothing to look in, the entry waits."""
    photo = _write(runtime, _PHOTO)
    store = _album(runtime, photo)
    runtime.locations.index_file.unlink()
    photo.rename(photo.with_name("IMG_9.jpg"))
    assert store.on_disk().missing[_ALBUM] == (_HOST,)
