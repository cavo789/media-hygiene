"""`tags` gives each photo its vector: photos only, copies once, Ctrl+C, bad files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.classify.models import MediaInput
from media_hygiene.index.meaning_rows import MeaningStore
from media_hygiene.index.repository import FactsRepository
from media_hygiene.meaning.clip import MODEL, SECONDS_PER_PHOTO
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.meaning import meaning_work, see_photos
from media_hygiene.services.subject_answers import Answering
from media_hygiene.services.tag_work import version_of
from tests.support.meaning import ColourImages

if TYPE_CHECKING:
    from pathlib import Path


def _files(tmp_path: Path) -> tuple[MediaInput, ...]:
    """A photo, its copy, a broken photo, a video."""
    blue = tmp_path / "blue.jpg"
    Image.new("RGB", (64, 48), (60, 120, 230)).save(blue)
    copy = tmp_path / "copy.jpg"
    copy.write_bytes(blue.read_bytes())
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"not a picture")
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"video")
    return tuple(
        MediaInput(path, tmp_path, path.stat().st_size, 7, digest=digest)
        for path, digest in (
            (blue, "same"),
            (copy, "same"),
            (broken, "other"),
            (video, "video"),
        )
    )


def test_photos_once_copies_free_bad_files_counted(tmp_path: Path) -> None:
    """The video is never looked at; the copy takes its twin's vector."""
    files = _files(tmp_path)
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        work = meaning_work(repository.connection, files)
        assert [file.path.name for file in work.missing] == [
            "blue.jpg",
            "copy.jpg",
            "broken.jpg",
        ]
        assert work.seconds_per_photo == SECONDS_PER_PHOTO
        assert work.estimate == 2 * SECONDS_PER_PHOTO  # the copy counted once
        answering = Answering(True, NullProgress())  # noqa: FBT003
        outcome = see_photos(repository.connection, (work, ColourImages()), answering)
        assert (outcome.seen, outcome.unreadable, outcome.stopped) == (2, 1, False)
        store = MeaningStore(repository.connection, MODEL)
        assert not store.missing(map(version_of, files[:2]))
        again = meaning_work(repository.connection, files)
        assert [file.path.name for file in again.missing] == ["broken.jpg"]
        assert again.seconds_per_photo == store.seconds_per_photo()


def test_ctrl_c_stops_between_two_photos(tmp_path: Path) -> None:
    """Asked to stop: nothing more is looked at, the next run goes on."""
    files = _files(tmp_path)
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        work = meaning_work(repository.connection, files)
        answering = Answering(True, NullProgress(), lambda: True)  # noqa: FBT003
        outcome = see_photos(repository.connection, (work, ColourImages()), answering)
        assert (outcome.seen, outcome.stopped) == (0, True)
        assert len(meaning_work(repository.connection, files).missing) == len(
            work.missing
        )
