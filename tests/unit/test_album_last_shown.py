"""0603: the PC writes when the TV showed an album; every phone reads it."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.services.home import home_page
from media_hygiene.share.album_edit import rename_album
from media_hygiene.share.album_follow import Lookup
from media_hygiene.share.album_shown import note_shown
from media_hygiene.share.album_store import AlbumsPlace, AlbumStore
from media_hygiene.share.albums import Album, AlbumsFile, read_albums, write_albums

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _saved(target: Path, *names: str) -> None:
    """Save albums of these names."""
    albums = tuple(Album(name=name) for name in names)
    write_albums(target, AlbumsFile(albums=albums))


def test_the_date_is_written_on_that_album_only(tmp_path: Path) -> None:
    """Whatever the case typed; read back from the disk, the other album untouched."""
    target = tmp_path / "albums.json"
    _saved(target, "Crete", "Rome")
    note_shown(target, "crete")
    back = read_albums(target)
    crete, rome = back.named("Crete"), back.named("Rome")
    assert crete
    assert rome
    assert isinstance(crete.last_shown, dt.datetime)
    assert rome.last_shown is None


def test_a_schema_2_file_is_read_and_has_no_date(tmp_path: Path) -> None:
    """A file saved before 0603 still opens."""
    target = tmp_path / "albums.json"
    target.write_text('{"version": 2, "albums": [{"name": "Crete"}]}', encoding="utf-8")
    album = read_albums(target).named("Crete")
    assert album
    assert album.last_shown is None


def test_an_album_gone_changes_nothing(tmp_path: Path) -> None:
    """Deleted since: the file stays as it was."""
    target = tmp_path / "albums.json"
    _saved(target, "Crete")
    before = target.read_bytes()
    note_shown(target, "Rome")
    assert target.read_bytes() == before


def test_a_file_that_cannot_be_saved_does_not_stop_the_show(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reports mounted `:ro`, or a broken file: no error, the show goes on."""
    target = tmp_path / "albums.json"
    _saved(target, "Crete")

    def refused(*_args: object) -> None:
        raise OSError

    monkeypatch.setattr("media_hygiene.share.album_shown.write_albums", refused)
    note_shown(target, "Crete")
    monkeypatch.undo()
    target.write_text("not json", encoding="utf-8")
    note_shown(target, "Crete")
    assert target.read_text(encoding="utf-8") == "not json"


def test_a_renamed_album_keeps_its_date(tmp_path: Path) -> None:
    """Stored by album: a rename from the albums page keeps it."""
    target = tmp_path / "albums.json"
    _saved(target, "Crete")
    note_shown(target, "Crete")
    store = AlbumStore(AlbumsPlace(target, "x"), _no_lookup(tmp_path))
    shelf = rename_album(store, ("Crete", "Crete 2023"))
    renamed = shelf.albums.named("Crete 2023")
    assert renamed
    assert renamed.last_shown


def _no_lookup(tmp_path: Path) -> Lookup:
    """An index that does not exist, for albums without files."""
    return Lookup(tmp_path / "index.db", HostPathMapper(tmp_path, ()))


def test_the_phone_reads_the_date_not_its_own_storage() -> None:
    """The shortcuts come from the list; nothing kept on a phone any more."""
    page = home_page(remote=True).decode()
    assert "album.last_shown" in page
    assert "tvRecent" not in page
