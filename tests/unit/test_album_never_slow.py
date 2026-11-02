"""Albums never slow a page (0547): the list never hashes, each entry followed once."""

from __future__ import annotations

import datetime as dt
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.index.schema import prepare
from media_hygiene.services.album_reader import AlbumReader
from media_hygiene.services.albums import album_store as store_of
from media_hygiene.share import album_follow, album_lost, album_store
from media_hygiene.share.albums import (
    ALBUMS_FILE,
    Album,
    AlbumEntry,
    AlbumsFile,
    write_albums,
)
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_follow import Followed, Lookup

_SIZE = 1234
_ADDED = dt.datetime(2026, 10, 31, tzinfo=dt.UTC)


def _runtime(tmp_path: Path, albums: int, entries: int) -> Runtime:
    """Albums whose files are all lost; 500 same-size files indexed without digest."""
    runtime = make_runtime(make_locations(tmp_path))
    with closing(sqlite3.connect(runtime.locations.index_file)) as connection:
        prepare(connection)
        connection.executemany(
            "INSERT INTO files (path, size, mtime_ns) VALUES (?, ?, 0)",
            [(f"/data/c/Other/{rank}.jpg", _SIZE) for rank in range(500)],
        )
        connection.commit()
    shelf = tuple(
        Album(
            name=f"Sent {number}",
            entries=tuple(
                AlbumEntry(
                    path=f"C:\\Lost\\{number}\\{rank}.jpg",
                    sha256="a" * 64,
                    size=_SIZE,
                    added=_ADDED,
                )
                for rank in range(entries)
            ),
        )
        for number in range(albums)
    )
    target = runtime.locations.reports_dir / ALBUMS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    write_albums(target, AlbumsFile(albums=shelf))
    return runtime


def test_a_list_of_lost_files_never_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """240 lost entries, 500 same-size files without digest: no file read in full."""
    runtime = _runtime(tmp_path, 1, 240)

    def refused(_path: Path) -> str:
        pytest.fail("a page hashed a file")

    monkeypatch.setattr("media_hygiene.share.album_follow.full_digest", refused)
    monkeypatch.setattr(album_lost, "search_later", lambda _store, _shelf: None)
    monkeypatch.setattr(
        "media_hygiene.services.album_reader.search_later", lambda _s, _h: None
    )
    reader = AlbumReader(runtime, cast("Executor", None))
    shown = cast("dict[str, list[dict[str, object]]]", reader.listing()[0])
    assert [album["name"] for album in shown["albums"]] == ["Sent 0"]


def test_six_albums_each_entry_followed_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The shelf is read once per listing, not once per album (no N² follow)."""
    runtime = _runtime(tmp_path, 6, 3)
    real = album_follow.follow
    followed: list[int] = []

    def counted(entries: tuple[AlbumEntry, ...], lookup: Lookup) -> Followed:
        followed.append(len(entries))
        return real(entries, lookup)

    monkeypatch.setattr(album_store, "follow", counted)
    monkeypatch.setattr(
        "media_hygiene.services.album_reader.search_later", lambda _s, _h: None
    )
    AlbumReader(runtime, cast("Executor", None)).listing()
    assert sum(followed) == 6 * 3


def test_the_background_search_is_asked_once_per_lost_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The next page load does not start the same search again."""
    runtime = _runtime(tmp_path, 1, 2)
    started: list[object] = []
    monkeypatch.setattr(album_lost, "_ASKED", set())
    monkeypatch.setattr(
        album_lost._POOL,  # noqa: SLF001  # pylint: disable=protected-access
        "submit",
        lambda *args: started.append(args),
    )
    store = store_of(runtime)
    for _load in range(3):
        album_lost.search_later(store, store.on_disk())
    assert len(started) == 1
