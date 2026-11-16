"""Photos given a place by hand: found where listed without reading them again."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from media_hygiene.config.face_refs import face_mapper
from media_hygiene.config.photo_ref import PhotoRef, content_id
from media_hygiene.config.place_photos import PlacePhotos
from media_hygiene.scan.hashing import full_digest
from media_hygiene.search.placed_where import placed_where

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_CONTENT = b"a photo of the beach"
_SIZE = len(_CONTENT)
_SHA = hashlib.sha256(_CONTENT).hexdigest()


def test_listed_path_and_size_need_no_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """At its path with its size: found, nothing read; a copy elsewhere: by digest."""
    host = "C:\\Photos\\beach.jpg"
    here = face_mapper().to_container(host)
    copy = tmp_path / "copy.jpg"
    copy.write_bytes(_CONTENT)
    read: list[Path] = []

    def counted(path: Path) -> str:
        read.append(path)
        return full_digest(path)

    monkeypatch.setattr("media_hygiene.classify.hand_placed.full_digest", counted)
    given = [
        PlacePhotos(
            place="Beach", photos=(PhotoRef(path=host, id=content_id(_SHA, _SIZE)),)
        )
    ]
    rows = [
        (str(here), _SIZE, None),
        (str(copy), _SIZE, None),
        (str(tmp_path / "x"), 9, None),
    ]
    found = placed_where(rows, given)
    assert found == {here: "Beach", copy: "Beach"}
    assert read == [copy]  # the listed photo itself was not read


def test_same_path_another_size_is_checked_by_content(tmp_path: Path) -> None:
    """The path listed, another size: not that photo (edited), never placed blindly."""
    host = "C:\\Photos\\beach.jpg"
    here = face_mapper().to_container(host)
    given = [
        PlacePhotos(
            place="Beach", photos=(PhotoRef(path=host, id=content_id(_SHA, _SIZE)),)
        )
    ]
    assert not placed_where([(str(here), _SIZE + 1, None)], given)
    del tmp_path
