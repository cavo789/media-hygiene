"""0839: the faces of a video, found on a few frames, kept once per person."""

from __future__ import annotations

import io
import sqlite3
from typing import TYPE_CHECKING

import pytest
from PIL import Image
from typer.testing import CliRunner

from media_hygiene.faces.models import FACE_MODEL
from media_hygiene.faces.video_faces import FACE_EDGE
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.schema import SCHEMA_VERSION, prepare
from media_hygiene.people.crops import CropJob, face_crop
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services import people as people_service
from media_hygiene.services.people import PeopleStep
from media_hygiene.services.subject_answers import Answering
from tests.support.cli import point_mounts, run
from tests.support.faces import FakeRecipe, coloured
from tests.support.media import FFMPEG, encode
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

pytestmark = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg writes the video")
# Person 0 (red) for one second, then person 2 (blue) for two: seen on five frames.
_RED_THEN_BLUE = (
    *("-f", "lavfi", "-i", "color=c=0xDC1E1E:s=160x120:d=1:r=10"),
    *("-f", "lavfi", "-i", "color=c=0x1E1EDC:s=160x120:d=2:r=10"),
    *("-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]", "-map", "[v]"),
    *("-pix_fmt", "yuv420p"),
)


@pytest.fixture
def video(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A photo and a video of two people, audited.

    Args:
        locations: The test mount points.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        The video, in the container.
    """
    point_mounts(locations, monkeypatch)
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    coloured(locations.data_dir / "c" / "Family" / "IMG_1.png", 1)
    clip = locations.data_dir / "c" / "Family" / "MVI_1.mp4"
    encode(clip, *_RED_THEN_BLUE)
    audited = run(CliRunner(), "audit")
    assert audited.exit_code == 0, audited.output
    return clip


def test_videos_are_left_out_unless_asked(locations: Locations, video: Path) -> None:
    """Without `[people] videos`, the run lists the photo only."""
    with PeopleStep(make_runtime(locations)) as people:
        assert video not in {photo.path for photo in people.plan(()).photos}


def test_a_video_gets_one_face_per_person_each_with_its_frame(
    locations: Locations, video: Path
) -> None:
    """Two people on five frames: two faces, a moment each, cut from that frame."""
    runtime = make_runtime(locations, {"people": {"videos": True}})
    answering = Answering(True, NullProgress())  # noqa: FBT003
    with PeopleStep(runtime) as people:
        work = people.plan(())
        assert video in {photo.path for photo in work.missing}
        outcome = people.find(work.missing, answering)
        assert outcome.analysed == len(work.missing)
        faces = FaceStore(people.store.connection, FACE_MODEL).faces()
        assert not people.plan(()).missing  # a video scanned is done: no turn to guess
    of_video = [face for face in faces if face.path == video]
    assert [face.number for face in of_video] == [0, 1]
    moments = [face.moment for face in of_video]
    assert all(moment is not None for moment in moments)
    assert (moments[0] or 9) < 1 < (moments[1] or 0)
    assert all(face.moment is None for face in faces if face.path != video)
    assert of_video[0].box.width == FACE_EDGE  # the frame's pixels, as analysed
    blue = face_crop(CropJob(video, of_video[1].box, of_video[1].moment))
    assert blue is not None
    with Image.open(io.BytesIO(blue)) as picture:
        middle = (picture.width // 2, picture.height // 2)
        pixel = picture.convert("RGB").getpixel(middle)
        assert isinstance(pixel, tuple)
        assert pixel[2] > pixel[0]  # blue, the frame of the second person


def test_an_index_of_version_23_gets_the_frames_table(tmp_path: Path) -> None:
    """Upgraded in place: the faces kept, `face_frames` added, the version set."""
    connection = sqlite3.connect(tmp_path / "index.sqlite")
    prepare(connection)
    connection.execute("DROP TABLE face_frames")
    connection.execute("PRAGMA user_version = 23")
    connection.execute(
        "INSERT INTO face_scans VALUES ('/data/c/a.jpg', 1, 2, 'm', 0, 0.1)"
    )
    connection.commit()
    prepare(connection)
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
    assert "face_frames" in tables
    assert connection.execute("SELECT COUNT(*) FROM face_scans").fetchone() == (1,)
    assert connection.execute("PRAGMA user_version").fetchone() == (SCHEMA_VERSION,)
    connection.close()
