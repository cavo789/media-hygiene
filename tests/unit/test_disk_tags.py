"""Many photos' tags at once: the same as one by one, each photo once."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.review.disk_tags import disk_tags
from media_hygiene.review.versioned import disk_tag

if TYPE_CHECKING:
    from pathlib import Path


def test_tags_side_by_side_match_one_by_one(tmp_path: Path) -> None:
    """Each photo's tag as `disk_tag` says; a repeat once; a missing one empty."""
    photos = [tmp_path / f"IMG_{n}.jpg" for n in range(5)]
    for n, photo in enumerate(photos):
        photo.write_bytes(b"x" * (n + 1))
    gone = tmp_path / "gone.jpg"
    tags = disk_tags([*photos, photos[0], gone])
    assert tags == {**{photo: disk_tag(photo) for photo in photos}, gone: ""}
    assert all(tags[photo] for photo in photos)


def test_one_photo_needs_no_thread(tmp_path: Path) -> None:
    """A single photo: its tag."""
    photo = tmp_path / "IMG.jpg"
    photo.write_bytes(b"x")
    assert disk_tags([photo]) == {photo: disk_tag(photo)}
