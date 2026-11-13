"""The turn guessed by `people` (0725), kept per version, and the lossless tag write."""

from __future__ import annotations

import io
import shutil
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from media_hygiene.actions.orientation_bytes import (
    NoOrientationError,
    with_orientation,
)
from media_hygiene.constants import MediaKind
from media_hygiene.faces.turn_guess import NO_TURN, Seen, turn_of
from media_hygiene.faces.worker import FaceJob, find_faces
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.turn_rows import TurnGuess, TurnStore
from media_hygiene.scan.models import MediaFile
from tests.support.faces import FakeRecipe, face_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.models import Face

MODEL = "test-model"
_MARK = (255, 0, 0)
_RED = 150


class _TopLeftFinder:
    """A face only when the red pixel is at the top left: the picture is upright."""

    def find(self, picture: Image.Image) -> tuple[Face, ...]:
        """Find the fake face."""
        red, green, _blue = picture.convert("RGB").getpixel((0, 0))  # type: ignore[misc]
        if red > _RED and green < _RED // 2:
            return (face_of(0, picture.size),)
        return ()


def _photo(path: Path, make: str | None, orientation: int | None = 1) -> Path:
    """A 40 x 20 photo, a red square at the top right (a quarter turn left)."""
    picture = Image.new("RGB", (40, 20))
    picture.paste(_MARK, (32, 0, 40, 8))
    exif = Image.Exif()
    if make:
        exif[0x010F] = make
    if orientation is not None:
        exif[0x0112] = orientation
    picture.save(path, "JPEG", quality=100, exif=exif)
    return path


def _stored(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")


def test_a_camera_photo_without_face_as_stored_is_proposed_a_turn(
    tmp_path: Path,
) -> None:
    """A camera photo is guessed; a picture without camera, or tagged, is not."""
    finder = _TopLeftFinder()
    camera = _photo(tmp_path / "P1.jpg", "Canon")
    assert turn_of(Seen(camera, _stored(camera), 0), finder) == 270
    collage = _photo(tmp_path / "c.jpg", None)
    assert turn_of(Seen(collage, _stored(collage), 0), finder) == NO_TURN
    tagged = _photo(tmp_path / "t.jpg", "Canon", 6)
    assert turn_of(Seen(tagged, _stored(tagged), 0), finder) == NO_TURN
    assert (
        turn_of(Seen(camera, _stored(camera), 1), finder) == NO_TURN
    )  # a face as stored


def test_turn_only_jobs_skip_photos_not_worth_guessing(tmp_path: Path) -> None:
    """No camera: answered from the header, faces not searched; degrees: whole."""
    plain = _photo(tmp_path / "plain.jpg", None)
    quick = find_faces(FaceJob(plain, 1, 1, FakeRecipe(), turn_only=True))
    assert quick is not None
    assert (quick.complete, quick.turn) == (False, NO_TURN)
    degrees = _photo(tmp_path / "deg.jpg", None, 90)
    whole = find_faces(FaceJob(degrees, 1, 1, FakeRecipe(), turn_only=True))
    assert whole is not None
    assert whole.complete
    full = find_faces(FaceJob(plain, 1, 1, FakeRecipe()))
    assert full is not None
    assert full.complete


def test_turns_are_kept_per_version_followed_and_forgotten(tmp_path: Path) -> None:
    """In-place write, atomic save, touch: a new mtime; a move follows; gone: gone."""
    path = tmp_path / "a.jpg"
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        repository.put(MediaFile(path, 10, 1, MediaKind.IMAGE), FileFacts())
        store = TurnStore(repository.connection, MODEL)
        assert not store.guessed(PhotoVersion(path, 10, 1))
        store.put(TurnGuess(path, 10, 1, 90))
        assert store.guessed(PhotoVersion(path, 10, 1))
        assert store.proposed() == ((path, 90),)
        # Turned by Apply, saved again or touched: a new version, guessed again.
        assert not store.guessed(PhotoVersion(path, 10, 2))
        assert not store.guessed(PhotoVersion(path, 11, 1))
        repository.put(MediaFile(path, 10, 2, MediaKind.IMAGE), FileFacts())
        assert not store.proposed()  # the old guess is not proposed any more
        repository.put(MediaFile(path, 10, 1, MediaKind.IMAGE), FileFacts())
        moved = tmp_path / "sorted" / "a.jpg"  # `sort`, `undo`, a rename seen
        repository.move([(str(path), str(moved))])
        assert store.proposed() == ((moved, 90),)
        assert not TurnStore(repository.connection, "other").proposed()
        repository.forget([str(moved)])  # the audit finds it gone
        assert not store.proposed()


def test_a_copy_keeping_its_mtime_is_guessed_on_its_own(tmp_path: Path) -> None:
    """A copy is another path: its own row, the original's untouched."""
    path = _photo(tmp_path / "a.jpg", "Canon")
    copy = tmp_path / "b.jpg"
    shutil.copy2(path, copy)
    seen = path.stat()
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        store = TurnStore(repository.connection, MODEL)
        store.put(TurnGuess(path, seen.st_size, seen.st_mtime_ns, 90))
        assert not store.guessed(PhotoVersion(copy, seen.st_size, seen.st_mtime_ns))


def test_orientation_write_is_lossless_and_undone_byte_for_byte(
    tmp_path: Path,
) -> None:
    """Two bytes change; the old code put back gives the very same file."""
    path = _photo(tmp_path / "a.jpg", "Canon", 1)
    before = path.read_bytes()
    turned, old = with_orientation(before, 6)
    assert old == 1
    assert len(turned) == len(before)
    assert sum(a != b for a, b in zip(before, turned, strict=True)) == 1
    path.write_bytes(turned)
    with Image.open(path) as image:
        assert image.getexif()[0x0112] == 6
        pixels = image.tobytes()
    with Image.open(io.BytesIO(before)) as original:
        assert pixels == original.tobytes()  # not encoded again
    back, code = with_orientation(path.read_bytes(), old)
    assert code == 6
    assert back == before


def test_orientation_write_refuses_what_it_cannot_patch(tmp_path: Path) -> None:
    """No tag, not a JPEG, a code outside EXIF: refused, nothing written."""
    untagged = _photo(tmp_path / "u.jpg", "Canon", None).read_bytes()
    with pytest.raises(NoOrientationError):
        with_orientation(untagged, 6)
    with pytest.raises(NoOrientationError):
        with_orientation(b"not a jpeg", 6)
    with pytest.raises(ValueError, match="orientation"):
        with_orientation(untagged, 90)
    big_endian = tmp_path / "m.tif"
    Image.new("RGB", (4, 4)).save(big_endian)
    with pytest.raises(NoOrientationError):
        with_orientation(big_endian.read_bytes(), 6)
