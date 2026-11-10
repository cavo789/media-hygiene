"""0673: tile pictures named after the file's version, kept by the browser for good.

One test per event that changes what a picture shows: each one must change its name
(or refuse the old one), never serve a stale picture under a name kept for good.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.schema import prepare
from media_hygiene.report import preview_cache
from media_hygiene.review.http import Response
from media_hygiene.review.respond import IMMUTABLE_S, write_response
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.pictures import Pictures
from media_hygiene.search.stable_pictures import parsed_name, tile_pictures

if TYPE_CHECKING:
    from pathlib import Path

_UPDATE = "UPDATE files SET path = ?, size = ?, mtime_ns = ? WHERE rowid = 1"


def _photo(path: Path, colour: str = "red") -> PhotoVersion:
    """Write a small JPEG and say its version."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 48), colour).save(path)
    stat = path.stat()
    return PhotoVersion(path, stat.st_size, stat.st_mtime_ns)


def _index(tmp_path: Path, photo: PhotoVersion) -> Path:
    """An index listing one photo, as row 1."""
    index = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        connection.execute(
            "INSERT INTO files (path, size, mtime_ns) VALUES (?, ?, ?)",
            (str(photo.path), photo.size, photo.mtime_ns),
        )
        connection.commit()
    return index


def _seen(index: Path, photo: PhotoVersion) -> None:
    """The index records the file's new version (an audit, `sort`, `undo`…)."""
    with closing(sqlite3.connect(index)) as connection:
        connection.execute(_UPDATE, (str(photo.path), photo.size, photo.mtime_ns))
        connection.commit()


def _ask(index: Path, path: str) -> Response:
    """Ask the search page's pictures for a path."""
    with SearchIndex.open(index) as opened, ThreadPoolExecutor(1) as pool:
        answer = asyncio.run(Pictures(opened, None, pool).answer(path))
    assert answer is not None
    return answer


def _thumb(photo: PhotoVersion) -> str:
    return tile_pictures(1, photo)["thumb"]


def test_a_picture_of_the_version_listed_is_kept_for_good(tmp_path: Path) -> None:
    """Named after the version the index lists, unchanged on disk: a year, immutable."""
    photo = _photo(tmp_path / "a.jpg")
    index = _index(tmp_path, photo)
    for name in tile_pictures(1, photo).values():
        answer = _ask(index, name)
        assert answer.status is HTTPStatus.OK
        assert answer.max_age == IMMUTABLE_S


def test_the_name_says_nothing_of_the_file(tmp_path: Path) -> None:
    """The tag is a hash: neither the folder nor the file's name shows."""
    photo = _photo(tmp_path / "Secret holidays" / "IMG_1.jpg")
    name = _thumb(photo)
    assert "Secret" not in name
    assert "IMG" not in name
    assert parsed_name(name.removeprefix("/thumb/").removesuffix(".jpg")) is not None


def test_a_file_edited_in_place_is_never_kept_under_its_old_name(
    tmp_path: Path,
) -> None:
    """Edited, not yet audited: shown, asked again; once audited, a new name."""
    photo = _photo(tmp_path / "a.jpg")
    index = _index(tmp_path, photo)
    old = _thumb(photo)
    edited = _photo(photo.path, "blue")
    os.utime(photo.path, ns=(photo.mtime_ns + 10**9, photo.mtime_ns + 10**9))
    edited = PhotoVersion(photo.path, edited.size, photo.mtime_ns + 10**9)
    answer = _ask(index, old)
    assert answer.status is HTTPStatus.OK
    assert answer.max_age == 0  # today's rule: no-cache, asked again
    _seen(index, edited)
    assert _thumb(edited) != old
    assert _ask(index, old).status is HTTPStatus.NOT_FOUND


def test_a_file_replaced_keeping_its_time_gets_a_new_name(tmp_path: Path) -> None:
    """Another picture copied over it, its modification time kept: the size differs."""
    photo = _photo(tmp_path / "a.jpg")
    index = _index(tmp_path, photo)
    old = _thumb(photo)
    Image.new("RGB", (640, 480), "green").save(photo.path)
    os.utime(photo.path, ns=(photo.mtime_ns, photo.mtime_ns))
    assert _ask(index, old).max_age == 0  # the disk no longer matches the name
    replaced = PhotoVersion(photo.path, photo.path.stat().st_size, photo.mtime_ns)
    _seen(index, replaced)
    assert _thumb(replaced) != old
    assert _ask(index, old).status is HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "moved_to",
    [
        "Renamed in Explorer/a.jpg",  # a folder renamed by the user
        "2015/2015-07 Holidays/a.jpg",  # `sort`, `undo`, `clean --repair`
        "quarantine/c/a.jpg",  # set aside: moved to the quarantine
    ],
)
def test_a_file_moved_or_renamed_gets_a_new_name(tmp_path: Path, moved_to: str) -> None:
    """The path is in the name: a move by the tool or by the user changes it."""
    photo = _photo(tmp_path / "a.jpg")
    index = _index(tmp_path, photo)
    old = _thumb(photo)
    target = tmp_path / moved_to
    target.parent.mkdir(parents=True)
    photo.path.rename(target)
    assert _ask(index, old).status is HTTPStatus.NOT_FOUND  # gone from its place
    moved = PhotoVersion(target, photo.size, photo.mtime_ns)
    _seen(index, moved)
    assert _thumb(moved) != old
    assert _ask(index, old).status is HTTPStatus.NOT_FOUND
    assert _ask(index, _thumb(moved)).max_age == IMMUTABLE_S


def test_a_preview_version_bump_renames_every_picture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Previews made differently: every name changes, the old ones are refused."""
    photo = _photo(tmp_path / "a.jpg")
    index = _index(tmp_path, photo)
    old = _thumb(photo)
    monkeypatch.setattr(preview_cache, "_VERSION", preview_cache._VERSION + 1)  # noqa: SLF001  # pylint: disable=protected-access
    assert _thumb(photo) != old
    assert _ask(index, old).status is HTTPStatus.NOT_FOUND


def test_a_key_given_to_another_file_refuses_the_old_name(tmp_path: Path) -> None:
    """A row of the index reused by another file: the old name is not its picture."""
    photo = _photo(tmp_path / "a.jpg")
    index = _index(tmp_path, photo)
    old = _thumb(photo)
    _seen(index, _photo(tmp_path / "b.jpg", "blue"))
    assert _ask(index, old).status is HTTPStatus.NOT_FOUND


@pytest.mark.parametrize("name", ["/thumb/9.jpg", "/thumb/x.jpg", "/thumb/1.a/b.jpg"])
def test_an_unknown_or_odd_name_is_not_found(tmp_path: Path, name: str) -> None:
    """No such key, no key, a tag that is not one: 404."""
    index = _index(tmp_path, _photo(tmp_path / "a.jpg"))
    assert _ask(index, name).status is HTTPStatus.NOT_FOUND


def test_a_name_without_version_keeps_the_rule_of_the_run(tmp_path: Path) -> None:
    """`/thumb/1.jpg` (the slideshow, the albums): asked again (`no-cache`)."""
    index = _index(tmp_path, _photo(tmp_path / "a.jpg"))
    answer = _ask(index, "/thumb/1.jpg")
    assert answer.status is HTTPStatus.OK
    assert answer.cacheable
    assert answer.max_age == 0


class _Writer:
    """Collects what a response writes."""

    def __init__(self) -> None:
        self.sent = b""

    def write(self, data: bytes) -> None:
        """Keep the bytes written."""
        self.sent += data

    async def drain(self) -> None:
        """Nothing to wait for."""


def test_a_picture_kept_for_good_is_said_immutable() -> None:
    """`Cache-Control: private, max-age=31536000, immutable`, without an `ETag`."""
    writer = _Writer()
    answer = Response(HTTPStatus.OK, b"x", max_age=IMMUTABLE_S)
    asyncio.run(write_response(writer, answer))  # type: ignore[arg-type]
    head = writer.sent.decode()
    assert "Cache-Control: private, max-age=31536000, immutable" in head
    assert "ETag" not in head
