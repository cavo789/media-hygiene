"""Files moved or renamed outside the tool keep what the cache knew (TODO 0147)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.faces.models import PhotoFaces
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.rematch import rematched
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.hashing import partial_digest
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.demo import build_demo
from tests.support.faces import face_of
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from media_hygiene.paths.locations import Locations

_MODEL: Final = "test-model"


def audit(locations: Locations) -> None:
    """Run an audit of the data mount point."""
    AuditService(make_runtime(locations), NullProgress()).run()


def listed(path: Path) -> MediaFile:
    """The file as the walk lists it."""
    stat = path.stat()
    return MediaFile(path, stat.st_size, stat.st_mtime_ns, MediaKind.IMAGE)


def test_a_renamed_folder_and_a_moved_file_are_not_checked_again(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rows, faces included, follow the files; no picture is decoded again."""
    build_demo(locations.data_dir)
    audit(locations)
    photo = next(path for path in sorted(locations.data_dir.rglob("*.jpg")))
    index = locations.index_file
    with FactsRepository.open(index) as repository:
        seen = listed(photo)
        faces = (face_of(0, (60, 60)),)
        FaceStore(repository.connection, _MODEL).put(
            PhotoFaces(photo, seen.size, seen.mtime_ns, faces, 0.5)
        )
    folder = photo.parent
    renamed = folder.with_name(folder.name + " (renamed)")
    folder.rename(renamed)
    moved = renamed / photo.name

    def forbidden(*_args: object) -> None:
        raise AssertionError

    for name in ("inspect_image", "read_image_metadata", "inspect_raw", "probe_video"):
        monkeypatch.setattr(f"media_hygiene.scan.file_check.{name}", forbidden)
    audit(locations)
    with FactsRepository.open(index) as repository:
        assert repository.get(listed(moved)).integrity_checked
        faces_now = FaceStore(repository.connection, _MODEL).faces()
        assert {face.path for face in faces_now} == {moved}


def test_same_size_and_time_is_not_enough(tmp_path: Path) -> None:
    """Another content (other partial digest), or another time: never paired."""
    gone = tmp_path / "gone.jpg"
    gone.write_bytes(b"a" * 100)
    other = tmp_path / "other.jpg"
    other.write_bytes(b"b" * 100)
    stat = gone.stat()
    os.utime(other, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    same = tmp_path / "same.jpg"
    same.write_bytes(b"a" * 100)
    os.utime(same, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1))
    with FactsRepository.open(None) as repository:
        repository.put(listed(gone), FileFacts().with_partial(partial_digest(gone)))
        gone.unlink()
        assert not rematched(repository.connection, [str(gone)], [listed(other)])
        assert not rematched(repository.connection, [str(gone)], [listed(same)])
        os.utime(same, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert rematched(repository.connection, [str(gone)], [listed(same)]) == [
            (str(gone), str(same))
        ]
