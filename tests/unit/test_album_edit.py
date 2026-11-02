"""Albums deleted, renamed, put back from the albums page (0499), read back."""

from __future__ import annotations

import asyncio
import json
import os
import time
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import phone_may
from media_hygiene.search.aside_filter import Kept
from media_hygiene.services.albums import album_desk, album_store
from media_hygiene.share.album_page import ALBUM_CHANGE_PATH
from media_hygiene.share.album_store import AlbumChange
from media_hygiene.share.album_trash import DELETED_FILE, KEEP_DAYS
from media_hygiene.share.albums import ALBUMS_FILE
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_api import AlbumAsked, AlbumDesk


@pytest.fixture
def runtime(tmp_path: Path) -> Runtime:
    """Three albums of one photo each."""
    runtime = make_runtime(make_locations(tmp_path))
    photo = runtime.locations.data_dir / "c/Photos/IMG_1.jpg"
    photo.parent.mkdir(parents=True)
    photo.write_bytes(b"crete")
    store = album_store(runtime)
    for name in ("Crete", "Rome", "Paris"):
        store.add(AlbumChange(name, (photo,)))
    return runtime


def _desk(runtime: Runtime) -> AlbumDesk:
    def nothing(_asked: AlbumAsked) -> Kept:
        return Kept(())

    return album_desk(runtime, nothing)


def _post(runtime: Runtime, body: dict[str, object]) -> tuple[HTTPStatus, str]:
    answer = asyncio.run(_desk(runtime).answer(json.dumps(body).encode()))
    said = json.loads(answer.body)
    return answer.status, str(said.get("message") or said.get("error"))


def _names(runtime: Runtime) -> list[str]:
    saved = json.loads((runtime.locations.reports_dir / ALBUMS_FILE).read_text())
    return [album["name"] for album in saved["albums"]]


def test_delete_one_album(runtime: Runtime) -> None:
    """Gone from the file; the photo stays; said from the disk."""
    status, message = _post(runtime, {"action": "delete", "names": ["rome"]})
    assert status is HTTPStatus.OK
    assert "1 album deleted" in message
    assert _names(runtime) == ["Crete", "Paris"]
    assert (runtime.locations.data_dir / "c/Photos/IMG_1.jpg").is_file()


def test_delete_several_then_undo(runtime: Runtime) -> None:
    """Two deleted, then put back from the copy kept next to the albums file."""
    _post(runtime, {"action": "delete", "names": ["Crete", "Paris"]})
    assert _names(runtime) == ["Rome"]
    assert (runtime.locations.reports_dir / DELETED_FILE).is_file()
    status, _message = _post(runtime, {"action": "restore"})
    assert status is HTTPStatus.OK
    assert _names(runtime) == ["Rome", "Crete", "Paris"]
    assert not (runtime.locations.reports_dir / DELETED_FILE).exists()
    assert _post(runtime, {"action": "restore"})[0] is HTTPStatus.CONFLICT


@pytest.mark.parametrize(
    ("days", "back"), [(KEEP_DAYS - 1, True), (KEEP_DAYS + 1, False)]
)
def test_undo_forgets_a_delete_older_than_keep_days(
    runtime: Runtime, days: int, *, back: bool
) -> None:
    """A delete of a month ago is forgotten: nothing to put back, its copy removed."""
    _post(runtime, {"action": "delete", "names": ["Rome"]})
    copy = runtime.locations.reports_dir / DELETED_FILE
    then = time.time() - days * 86_400
    os.utime(copy, (then, then))
    status, _message = _post(runtime, {"action": "restore"})
    assert (status is HTTPStatus.OK) is back
    assert ("Rome" in _names(runtime)) is back
    assert not copy.exists()


def test_rename(runtime: Runtime) -> None:
    """The new name, single spaces, read back; the album found by it at once."""
    status, message = _post(
        runtime, {"action": "rename", "album": "rome", "to": "Rome  2024"}
    )
    assert status is HTTPStatus.OK
    assert "Rome 2024" in message
    assert _names(runtime) == ["Crete", "Rome 2024", "Paris"]
    assert album_store(runtime).on_disk().albums.named("rome 2024") is not None


@pytest.mark.parametrize("to", ["paris", "", 'a "quote"'])
def test_rename_refused(runtime: Runtime, to: str) -> None:
    """Another album's name (whatever its case), or not a name: nothing changes."""
    status, _message = _post(runtime, {"action": "rename", "album": "Rome", "to": to})
    assert status is HTTPStatus.CONFLICT
    assert _names(runtime) == ["Crete", "Rome", "Paris"]


def test_a_phone_may_not_change_the_albums() -> None:
    """Read-only off the PC: the albums' POST is not one a phone may send."""
    request = Request("POST", ALBUM_CHANGE_PATH, {}, b"{}")
    assert not phone_may(request)
