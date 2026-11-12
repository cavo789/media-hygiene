"""0701: the pictures of every tile page, named after the file's version (`?v=`).

One test per event that changes what a picture shows (edit in place, replace keeping
the time, atomic save, `touch`, rename/move, preview version bump, file gone): each one
must change the address, and the old address must never be kept for good.
"""

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from media_hygiene.constants import MediaKind
from media_hygiene.report import preview_cache
from media_hygiene.review.local_app import jpeg_response
from media_hygiene.review.respond import IMMUTABLE_S
from media_hygiene.review.versioned import (
    asked_from,
    kept_for_good,
    versioned,
    versioned_on_disk,
)
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Response

_URL = "/preview/3.jpg"


def _photo(path: Path, colour: str = "red") -> Path:
    """Write a small JPEG."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 48), colour).save(path)
    return path


def _query(url: str) -> str:
    """What follows the `?` of an address."""
    return url.partition("?")[2]


def _render(source: Path) -> bytes:
    """The picture of a file: its bytes, enough here."""
    return source.read_bytes()


async def _served(url: str, source: Path) -> Response:
    """Answer an address as the server does: its tag remembered, then rendered."""
    asked_from(_query(url))
    with ThreadPoolExecutor(1) as executor:
        return await jpeg_response(executor, _render, source)


def _kept(url: str, source: Path) -> bool:
    """Whether the browser may keep this address's picture for good."""
    return asyncio.run(_served(url, source)).max_age == IMMUTABLE_S


def test_the_version_listed_is_kept_for_good(tmp_path: Path) -> None:
    """The version listed is kept for good."""
    source = _photo(tmp_path / "a.jpg")
    url = versioned_on_disk(_URL, source)
    assert url.startswith(f"{_URL}?v=")
    assert _kept(url, source)


def test_the_version_audited_names_the_same_address(tmp_path: Path) -> None:
    """The version audited names the same address."""
    source = _photo(tmp_path / "a.jpg")
    stat = source.stat()
    audited = MediaFile(source, stat.st_size, stat.st_mtime_ns, MediaKind.IMAGE)
    assert versioned(_URL, audited) == versioned_on_disk(_URL, source)


def test_an_address_without_version_keeps_the_rule_of_the_run(tmp_path: Path) -> None:
    """An address without version keeps the rule of the run."""
    source = _photo(tmp_path / "a.jpg")
    answer = asyncio.run(_served(_URL, source))
    assert answer.status is HTTPStatus.OK
    assert answer.cacheable
    assert answer.max_age == 0


def test_a_file_edited_in_place_is_never_kept_under_its_old_address(
    tmp_path: Path,
) -> None:
    """A file edited in place is never kept under its old address."""
    source = _photo(tmp_path / "a.jpg")
    old = versioned_on_disk(_URL, source)
    _photo(source, "blue")
    assert versioned_on_disk(_URL, source) != old
    assert not _kept(old, source)


def test_a_file_replaced_keeping_its_time_gets_a_new_address(tmp_path: Path) -> None:
    """A file replaced keeping its time gets a new address."""
    source = _photo(tmp_path / "a.jpg")
    old = versioned_on_disk(_URL, source)
    stat = source.stat()
    source.write_bytes(source.read_bytes() + b"\0")  # another size, same time
    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert versioned_on_disk(_URL, source) != old
    assert not _kept(old, source)


def test_an_atomic_save_gets_a_new_address(tmp_path: Path) -> None:
    """An atomic save gets a new address."""
    source = _photo(tmp_path / "a.jpg")
    old = versioned_on_disk(_URL, source)
    other = _photo(tmp_path / "new.jpg", "green")
    os.utime(other, ns=(1, 10**18))
    other.replace(source)  # a new inode under the same name
    assert not _kept(old, source)


def test_a_touch_gets_a_new_address(tmp_path: Path) -> None:
    """A touch gets a new address."""
    source = _photo(tmp_path / "a.jpg")
    old = versioned_on_disk(_URL, source)
    os.utime(source, ns=(1, source.stat().st_mtime_ns + 1_000_000_000))
    assert versioned_on_disk(_URL, source) != old
    assert not _kept(old, source)


def test_a_file_renamed_or_moved_gets_a_new_address(tmp_path: Path) -> None:
    """A file renamed or moved gets a new address."""
    source = _photo(tmp_path / "a.jpg")
    old = versioned_on_disk(_URL, source)
    moved = tmp_path / "elsewhere" / "b.jpg"
    moved.parent.mkdir()
    source.rename(moved)
    assert versioned_on_disk(_URL, moved) != old
    assert not _kept(old, moved)


def test_a_preview_version_bump_renames_every_picture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A preview version bump renames every picture."""
    source = _photo(tmp_path / "a.jpg")
    old = versioned_on_disk(_URL, source)
    monkeypatch.setattr(preview_cache, "_VERSION", 999)
    assert versioned_on_disk(_URL, source) != old
    assert not _kept(old, source)


def test_a_file_gone_keeps_its_address_plain_and_is_never_kept(tmp_path: Path) -> None:
    """A file gone keeps its address plain and is never kept."""
    gone = tmp_path / "gone.jpg"
    assert versioned_on_disk(_URL, gone) == _URL
    asked_from("v=0f3a")
    assert not kept_for_good(gone)


@pytest.mark.parametrize("query", ["", "v=", "v=../x", "w=abc", "v=a&b=c"])
def test_an_odd_query_is_never_kept_for_good(tmp_path: Path, query: str) -> None:
    """An odd query is never kept for good."""
    source = _photo(tmp_path / "a.jpg")
    asked_from(query)
    assert not kept_for_good(source)
