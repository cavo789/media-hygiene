"""`tags` gives each photo its vector: photos only, copies once, Ctrl+C, bad files."""

from __future__ import annotations

from pathlib import Path

import pillow_heif
import pytest
from PIL import Image

from media_hygiene.classify.models import MediaInput
from media_hygiene.console.meaning_view import left_aside_lines
from media_hygiene.index.meaning_rows import MeaningStore
from media_hygiene.index.repository import FactsRepository
from media_hygiene.meaning.clip import MODEL, SECONDS_PER_PHOTO
from media_hygiene.meaning.pace import PhotoPace, fitted_pace
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.meaning import (
    MeaningOutcome,
    MeaningWork,
    meaning_work,
    see_photos,
)
from media_hygiene.services.subject_answers import Answering
from media_hygiene.services.tag_work import version_of
from tests.support.meaning import ColourImages


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
        assert work.pace == PhotoPace(SECONDS_PER_PHOTO)
        assert work.estimate == 2 * SECONDS_PER_PHOTO  # the copy counted once
        answering = Answering(True, NullProgress())  # noqa: FBT003
        outcome = see_photos(repository.connection, (work, ColourImages()), answering)
        assert (outcome.seen, outcome.absent, outcome.stopped) == (2, 0, False)
        assert outcome.unreadable == [files[2].path]
        store = MeaningStore(repository.connection, MODEL)
        assert not store.missing(map(version_of, files[:2]))
        again = meaning_work(repository.connection, files)
        assert [file.path.name for file in again.missing] == ["broken.jpg"]
        assert again.seconds_per_photo == again.pace.base


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


def _input(path: Path, size: int | None = None) -> MediaInput:
    """A file of the index, its size given when it is not on the disk."""
    known = path.stat().st_size if size is None else size
    return MediaInput(path, path.parent, known, 7, digest=path.name)


def test_a_heic_gets_its_vector_without_the_audits_workers(tmp_path: Path) -> None:
    """The opener is installed by the run itself: 436 HEIC of a real library failed."""
    photo = tmp_path / "phone.heic"
    picture = Image.new("RGB", (64, 48), (60, 120, 230))
    pillow_heif.from_pillow(picture).save(photo)
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        work = meaning_work(repository.connection, (_input(photo),))
        answering = Answering(True, NullProgress())  # noqa: FBT003
        outcome = see_photos(repository.connection, (work, ColourImages()), answering)
    assert (outcome.seen, outcome.unreadable) == (1, [])


def test_a_photo_gone_is_not_called_undecodable(tmp_path: Path) -> None:
    """Deleted since the audit: counted apart, and tried again at the next run."""
    gone = _input(tmp_path / "gone.jpg", 10)
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        work = meaning_work(repository.connection, (gone,))
        answering = Answering(True, NullProgress())  # noqa: FBT003
        outcome = see_photos(repository.connection, (work, ColourImages()), answering)
        assert (outcome.absent, outcome.unreadable) == (1, [])
        assert meaning_work(repository.connection, (gone,)).missing == (gone,)


def test_undecodable_photos_are_named_the_rest_counted() -> None:
    """Twenty names as the user sees them, then how many more; and those not there."""
    bad = [Path(f"/data/c/Photos/{number}.jpg") for number in range(22)]
    outcome = MeaningOutcome(unreadable=bad, absent=3)
    lines = left_aside_lines(outcome, HostPathMapper(Path("/data")))
    assert "22" in lines[0]
    assert lines[1].strip() == r"C:\Photos\0.jpg".replace("\\\\", "\\")
    assert "2" in lines[21]
    assert "3" in lines[22]
    assert not left_aside_lines(MeaningOutcome(), HostPathMapper(Path("/data")))


def test_the_pace_follows_the_size_of_the_files() -> None:
    """Timed on small photos, the estimate of large ones is not the small ones' pace."""
    megabyte = 1_000_000
    timed = [(size * 10_000, 0.03 + 0.01 * size / 100) for size in range(1, 201)]
    pace = fitted_pace(timed)
    assert pace is not None
    assert pace.seconds(5 * megabyte) == pytest.approx(0.08)
    photos = tuple(
        MediaInput(Path(f"/p/{n}.jpg"), Path("/p"), 5 * megabyte, 7, digest=str(n))
        for n in range(10)
    )
    assert MeaningWork(photos, pace).estimate == pytest.approx(0.8)
    assert MeaningWork(photos, pace).seconds_per_photo == pytest.approx(0.08)
    assert MeaningWork((), pace).seconds_per_photo == pace.base


def test_a_flat_median_when_size_explains_nothing() -> None:
    """Few photos, one size, or times falling with the size: no line."""
    assert fitted_pace(()) is None
    assert fitted_pace([(1, 2.0), (2, 4.0)]) == PhotoPace(3.0)
    assert fitted_pace([(5, 1.0)] * 200) == PhotoPace(1.0)
    falling = [(size, 1.0 - size / 1000) for size in range(1, 201)]
    pace = fitted_pace(falling)
    assert pace is not None
    assert pace.per_byte == 0.0
