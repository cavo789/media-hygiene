"""`albums.json` (0295): named albums, saved at once, read back, a schema version."""

from __future__ import annotations

import codecs
import json
from typing import TYPE_CHECKING

import pytest

from media_hygiene.services.albums import album_store
from media_hygiene.share.album_store import AlbumChange
from media_hygiene.share.albums import (
    ALBUMS_FILE,
    AlbumsError,
    AlbumsFile,
    read_albums,
)
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


@pytest.fixture
def runtime(tmp_path: Path) -> Runtime:
    """A runtime whose folders lie under the test's folder."""
    return make_runtime(make_locations(tmp_path))


def _photos(runtime: Runtime, *names: str) -> tuple[Path, ...]:
    """Photos in two folders of the data folder."""
    paths = []
    for name in names:
        path = runtime.locations.data_dir / "c" / "Photos" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        paths.append(path)
    return tuple(paths)


def test_an_album_holds_photos_of_several_folders_and_nothing_else_changes(
    runtime: Runtime,
) -> None:
    """Only `albums.json` is written; the photos stay where and as they were."""
    photos = _photos(runtime, "Day 1/a.jpg", "Day 2/b.jpg")
    before = {path: path.read_bytes() for path in photos}
    store = album_store(runtime)
    shelf = store.add(AlbumChange("Crete  2023", photos))
    store.add(AlbumChange("crete 2023", photos[:1]))  # the same album, the same file
    assert [album.name for album in shelf.albums.albums] == ["Crete 2023"]
    saved = json.loads((runtime.locations.reports_dir / ALBUMS_FILE).read_text())
    assert saved["version"] == 1
    assert [entry["path"] for entry in saved["albums"][0]["entries"]] == [
        "C:\\Photos\\Day 1\\a.jpg",
        "C:\\Photos\\Day 2\\b.jpg",
    ]
    assert {path: path.read_bytes() for path in photos} == before
    assert sorted(p.name for p in runtime.locations.reports_dir.iterdir()) == [
        ALBUMS_FILE
    ]


def test_taking_files_out_and_an_empty_album_goes(runtime: Runtime) -> None:
    """The other albums are kept, in their order."""
    photos = _photos(runtime, "a.jpg", "b.jpg")
    store = album_store(runtime)
    store.add(AlbumChange("First", photos))
    store.add(AlbumChange("Second", photos[:1]))
    shelf = store.remove(AlbumChange("first", photos[:1]))
    assert [len(a.entries) for a in shelf.albums.albums] == [1, 1]
    shelf = store.remove(AlbumChange("First", photos[1:]))
    assert [album.name for album in read_albums(store.place.target).albums] == [
        "Second"
    ]
    with pytest.raises(AlbumsError, match="No album named"):
        store.remove(AlbumChange("Third", photos))


@pytest.mark.parametrize("name", ["", "   ", 'The "best"', "x" * 81])
def test_a_name_an_album_cannot_have(runtime: Runtime, name: str) -> None:
    """Empty, too long, or with a double quote (pasted in a command)."""
    with pytest.raises(AlbumsError, match="characters"):
        album_store(runtime).add(AlbumChange(name, _photos(runtime, "a.jpg")))


def test_a_file_that_is_not_an_albums_file_is_refused(tmp_path: Path) -> None:
    """Said, with what to do; a BOM written by Notepad is fine."""
    target = tmp_path / ALBUMS_FILE
    target.write_text("{}", encoding="utf-8")
    assert read_albums(target) == AlbumsFile()
    target.write_bytes(codecs.BOM_UTF8 + b'{"version": 1, "albums": []}')
    assert read_albums(target) == AlbumsFile()
    target.write_text('{"version": 2}', encoding="utf-8")
    with pytest.raises(AlbumsError, match="not a valid albums file"):
        read_albums(target)
    double = {"albums": [{"name": "A"}, {"name": "a"}]}
    target.write_text(json.dumps(double), encoding="utf-8")
    with pytest.raises(AlbumsError):
        read_albums(target)
    assert read_albums(tmp_path / "none.json") == AlbumsFile()
