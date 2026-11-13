"""A photo taken out, then put back by the toast's Undo at its old place (0726)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.services.albums import album_store
from media_hygiene.share.album_store import AlbumChange, AlbumStore
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

_NAME = "Crete"


def _five(tmp_path: Path) -> tuple[AlbumStore, tuple[Path, ...]]:
    runtime = make_runtime(make_locations(tmp_path))
    folder = runtime.locations.data_dir / "c/Photos"
    folder.mkdir(parents=True)
    photos = tuple(folder / f"IMG_{n}.jpg" for n in range(1, 6))
    for photo in photos:
        photo.write_bytes(photo.name.encode())
    store = album_store(runtime)
    store.add(AlbumChange(_NAME, photos))
    return store, photos


def _order(store: AlbumStore) -> list[str]:
    album = store.on_disk().albums.named(_NAME)
    assert album is not None
    return [
        entry.path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1] for entry in album.entries
    ]


def _out(store: AlbumStore, photo: Path) -> int:
    return store.remove(AlbumChange(_NAME, (photo,))).taken[0]


def test_second_of_five_comes_back_second(tmp_path: Path) -> None:
    """Removed at 1, Undo puts it at 1."""
    store, photos = _five(tmp_path)
    before = _order(store)
    at = _out(store, photos[1])
    assert at == 1
    store.add(AlbumChange(_NAME, (photos[1],), at))
    assert _order(store) == before


def test_several_out_then_undone_keep_their_order(tmp_path: Path) -> None:
    """Two taken out, each undone (last first): the album as it was."""
    store, photos = _five(tmp_path)
    before = _order(store)
    first = _out(store, photos[1])
    second = _out(store, photos[3])
    store.add(AlbumChange(_NAME, (photos[3],), second))
    store.add(AlbumChange(_NAME, (photos[1],), first))
    assert _order(store) == before


def test_beyond_the_end_is_appended(tmp_path: Path) -> None:
    """The album got shorter meanwhile: no error, the photo goes last."""
    store, photos = _five(tmp_path)
    at = _out(store, photos[3])
    store.remove(AlbumChange(_NAME, photos[:3]))
    store.add(AlbumChange(_NAME, (photos[3],), at))
    assert _order(store) == ["IMG_5.jpg", "IMG_4.jpg"]


def test_no_place_is_appended(tmp_path: Path) -> None:
    """*Add to an album* sends no place: the end, as before."""
    store, photos = _five(tmp_path)
    _out(store, photos[0])
    store.add(AlbumChange(_NAME, (photos[0],)))
    assert _order(store)[-1] == "IMG_1.jpg"
