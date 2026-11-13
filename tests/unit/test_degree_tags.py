"""Orientation tags in degrees (0724): applied, only those previews made again."""

from __future__ import annotations

import hashlib
import os
import shutil
from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.people.crops import upright_size
from media_hygiene.report import preview_cache, thumbnails
from media_hygiene.report.preview_cache import PreviewJob, cached_preview, preview_key
from media_hygiene.report.thumbnails import upright_picture
from media_hygiene.scan.degree_tags import degree_tagged

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_MARK = (255, 0, 0)
_EDGE = 64


def _photo(path: Path, orientation: int | None) -> Path:
    """A 40 x 20 photo, a red square at its top left as stored."""
    picture = Image.new("RGB", (40, 20))
    picture.paste(_MARK, (0, 0, 8, 8))
    exif = Image.Exif()
    if orientation is not None:
        exif[0x0112] = orientation
    picture.save(path, "JPEG", quality=100, exif=exif)
    return path


def _red_at(picture: Image.Image, where: tuple[int, int]) -> bool:
    red, green, _blue = picture.getpixel(where)  # type: ignore[misc]
    return red > 150 and green < 75


def test_degree_tags_are_applied_like_their_codes(tmp_path: Path) -> None:
    """`90` is code 6 (a quarter turn clockwise), `180` is code 3."""
    quarter = upright_picture(_photo(tmp_path / "q.jpg", 90))
    assert quarter.size == (20, 40)
    assert _red_at(quarter, (19, 0))  # top left turned clockwise: top right
    assert quarter.tobytes() == upright_picture(_photo(tmp_path / "6.jpg", 6)).tobytes()
    half = upright_picture(_photo(tmp_path / "h.jpg", 180))
    assert _red_at(half, (39, 19))
    assert upright_size(tmp_path / "q.jpg") == (20, 40)  # the face boxes' frame
    plain = upright_picture(_photo(tmp_path / "p.jpg", None))
    assert _red_at(plain, (0, 0))


def test_only_degree_tagged_previews_get_a_new_name(tmp_path: Path) -> None:
    """The other photos keep their preview: none is made again."""
    plain = PreviewJob(_photo(tmp_path / "p.jpg", 1), _EDGE, tmp_path)
    tagged = PreviewJob(_photo(tmp_path / "t.jpg", 90), _EDGE, tmp_path)
    assert not degree_tagged(plain.source)
    assert degree_tagged(tagged.source)
    assert not degree_tagged(tmp_path / "gone.jpg")
    old = "1\0{}\0{}\0{}\0{}"  # the name of a preview before 0724
    stat = plain.source.stat()
    key = old.format(plain.source, stat.st_size, stat.st_mtime_ns, _EDGE)
    assert preview_key(plain, stat.st_size, stat.st_mtime_ns).startswith(
        hashlib.sha256(key.encode()).hexdigest()[:32]
    )
    tag = tagged.source.stat()
    key = old.format(tagged.source, tag.st_size, tag.st_mtime_ns, _EDGE)
    assert not preview_key(tagged, tag.st_size, tag.st_mtime_ns).startswith(
        hashlib.sha256(key.encode()).hexdigest()[:32]
    )


def test_tag_written_later_keeping_the_mtime_gets_a_new_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """In place, atomic save, touch back, a copy keeping its mtime, a file gone."""
    made: list[Path] = []
    real = thumbnails.jpeg_preview

    def counting(source: Path, edge: int) -> bytes | None:
        made.append(source)
        return real(source, edge)

    monkeypatch.setattr(preview_cache, "jpeg_preview", counting)
    cache = tmp_path / "cache"
    cache.mkdir()
    photo = _photo(tmp_path / "a.jpg", 1)
    job = PreviewJob(photo, _EDGE, cache)
    cached_preview(job)
    cached_preview(job)
    assert made == [photo]  # kept: made once
    seen = photo.stat()
    saved = _photo(tmp_path / "new.jpg", 90)
    saved.replace(photo)  # atomic save of a tag in degrees, the mtime put back
    os.utime(photo, ns=(seen.st_atime_ns, seen.st_mtime_ns))
    assert cached_preview(job) is not None
    assert made == [photo, photo]  # read when made: a new preview
    copy = tmp_path / "copy.jpg"
    shutil.copy2(photo, copy)  # a copy keeping the mtime: its own preview
    cached_preview(PreviewJob(copy, _EDGE, cache))
    assert made == [photo, photo, copy]
    photo.unlink()
    assert cached_preview(job) is None
