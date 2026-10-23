"""`shrink`: the heavy videos listed, lightened, the originals set aside, then undone.

Synthetic clips only, encoded by the test: MJPEG with PCM sound in AVI (an old camera),
and a phone's H.264, never a real video.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.actions import shrink as shrink_actions
from media_hygiene.actions.journal import read_journal
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.not_worth import not_worth
from media_hygiene.services import shrink as shrink_service
from media_hygiene.services.phone_known import PhoneQuery, known_of
from media_hygiene.services.phone_plan import AsideState, PhoneFile
from tests.support.cli import point_mounts, run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from typer.testing import Result

    from media_hygiene.paths.locations import Locations

FFMPEG: Final = shutil.which("ffmpeg") or "ffmpeg"
_TAGS: Final = (
    "-metadata",
    "creation_time=2015-07-14T10:00:00Z",
    "-metadata",
    "location=+50.8466+004.3528/",
)
_MTIME: Final = 1_436_868_000_000_000_000  # 2015-07-14
_CAMERA: Final = "c/Videos/Camera/clip.avi"
_PHONE: Final = "c/Videos/Phone/phone.mp4"
_KEPT: Final = "c/Videos/Kept/kept.avi"

pytestmark = pytest.mark.skipif(
    subprocess.run(  # noqa: S603  # a fixed command
        (FFMPEG, "-hide_banner", "-encoders"), capture_output=True, check=False
    ).stdout.find(b"libx264")
    < 0,
    reason="this ffmpeg cannot encode H.264",
)


def _clip(path: Path, codec: tuple[str, ...], tone: int = 440) -> Path:
    """Encode a 3 s clip with sound and a camera's tags, dated 2015."""
    path.parent.mkdir(parents=True, exist_ok=True)
    picture = ("-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25:duration=3")
    sound = ("-f", "lavfi", "-i", f"sine=frequency={tone}:duration=3")
    command = (FFMPEG, "-v", "error", "-y", *picture, *sound, *codec, *_TAGS, str(path))
    subprocess.run(command, check=True)  # noqa: S603  # fixed arguments
    os.utime(path, ns=(_MTIME, _MTIME))
    return path


@pytest.fixture
def cli(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """A camera's MJPEG clip with its sidecar, a phone's H.264, one protected clip."""
    point_mounts(locations, monkeypatch)
    mjpeg = ("-c:v", "mjpeg", "-q:v", "2", "-c:a", "pcm_s16le")
    camera = _clip(locations.data_dir / _CAMERA, mjpeg)
    camera.with_name("clip.avi.xmp").write_text("<x:xmpmeta/>")
    _clip(locations.data_dir / _KEPT, mjpeg, tone=880)  # not a copy of the camera's
    _clip(locations.data_dir / _PHONE, ("-c:v", "libx264", "-c:a", "aac"))
    locations.config_file.write_text(
        "[folders]\nprotected = ['C:\\Videos\\Kept']\n", encoding="utf-8"
    )
    runner = CliRunner()
    assert run(runner, "audit").exit_code == 0
    return runner


def _shrink(cli: CliRunner, *args: str) -> Result:
    """Run `shrink`, then check it ended well."""
    result = run(cli, "shrink", *args)
    assert result.exit_code == 0, result.output
    return result


def test_the_list_changes_nothing(cli: CliRunner, locations: Locations) -> None:
    """The MJPEG clip only: not the phone's, not the protected one; nothing moves."""
    said = " ".join(_shrink(cli).output.split())
    assert "1 video worth lightening" in said
    assert "clip.avi" in said
    assert "phone.mp4" not in said
    assert "kept.avi" not in said
    assert "shrink --apply" in said
    assert (locations.data_dir / _CAMERA).is_file()


def test_lightened_kept_dated_then_undone(cli: CliRunner, locations: Locations) -> None:
    """MP4 in place, same date and sidecar; the original in the quarantine; undo."""
    camera = locations.data_dir / _CAMERA
    size = camera.stat().st_size
    said = " ".join(_shrink(cli, "--apply", "--yes").output.split())
    assert "1 video lightened" in said
    light = camera.with_suffix(".mp4")
    assert not camera.exists()
    assert light.stat().st_size < size * 0.7
    assert light.stat().st_mtime_ns == _MTIME
    assert light.with_name("clip.mp4.xmp").is_file()
    assert not camera.with_name("clip.avi.xmp").exists()
    (journal,) = locations.journal_dir.glob("*.jsonl")
    entries = read_journal(journal)
    aside = next(e for e in entries if e.action is ActionKind.QUARANTINE_SHRUNK)
    assert aside.quarantine is not None
    assert Path(aside.quarantine).stat().st_size == size
    assert run(cli, "undo").exit_code == 0
    assert camera.stat().st_size == size
    assert camera.with_name("clip.avi.xmp").is_file()
    assert not light.exists()


def test_not_worth_it_is_left_and_remembered(
    cli: CliRunner, locations: Locations
) -> None:
    """A gain asked too high: the clip stays, and the next list leaves it out."""
    text = locations.config_file.read_text(encoding="utf-8")
    locations.config_file.write_text(text + "[shrink]\nmin_gain_percent = 95\n")
    said = " ".join(_shrink(cli, "--apply", "--yes").output.split())
    assert "1 video not worth it" in said
    assert (locations.data_dir / _CAMERA).is_file()
    assert not list((locations.data_dir / "c/Videos/Camera").glob("*.tmp"))
    assert "No video worth lightening" in _shrink(cli).output


def test_an_edited_lighter_video_is_kept_by_undo(
    cli: CliRunner, locations: Locations
) -> None:
    """Changed since: undo keeps it and says why; the original comes back beside."""
    _shrink(cli, "--apply", "--yes")
    light = (locations.data_dir / _CAMERA).with_suffix(".mp4")
    light.write_bytes(light.read_bytes() + b"edited")
    said = " ".join(run(cli, "undo").output.split())
    assert "changed since" in said
    assert light.is_file()
    assert (locations.data_dir / _CAMERA).is_file()


def test_the_phone_s_copy_of_an_original_is_never_imported_again(
    cli: CliRunner, locations: Locations
) -> None:
    """The phone still holds the original: `mh phone` sees it set aside, not new."""
    camera = locations.data_dir / _CAMERA
    size = camera.stat().st_size
    _shrink(cli, "--apply", "--yes")
    original = PhoneFile(PurePosixPath("Camera/clip.avi"), size, "2015-07-14")
    query = PhoneQuery((original,))
    known = known_of(make_runtime(locations), query)
    aside = known.set_aside[original.key]
    assert aside.action == ActionKind.QUARANTINE_SHRUNK.value
    assert aside.state is AsideState.QUARANTINE
    assert original.key not in known.library


def test_an_original_copied_back_goes_back_to_the_quarantine(
    cli: CliRunner, locations: Locations
) -> None:
    """A backup copied the original back: `clean` sets it aside again."""
    _shrink(cli, "--apply", "--yes")
    (journal,) = locations.journal_dir.glob("*.jsonl")
    entries = read_journal(journal)
    aside = next(e for e in entries if e.action is ActionKind.QUARANTINE_SHRUNK)
    assert aside.quarantine is not None
    back = locations.data_dir / "c/Videos/Phone/clip.avi"
    shutil.copy2(aside.quarantine, back)
    result = run(cli, "clean", "--yes")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "you had already set aside is back" in said
    assert not back.exists()


def test_a_rename_that_fails_is_said_and_undone(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The original already aside: the run says where both are; undo brings it back."""
    camera = locations.data_dir / _CAMERA

    def refuse(source: Path, target: Path) -> None:
        if target.suffix == ".mp4":
            raise PermissionError(13, "Permission denied")
        source.rename(target)

    monkeypatch.setattr(shrink_actions, "rename_no_replace", refuse)
    said = " ".join(_shrink(cli, "--apply", "--yes").output.split())
    assert "'undo' brings it back" in said
    assert not camera.exists()
    monkeypatch.undo()
    point_mounts(locations, monkeypatch)
    assert run(cli, "undo").exit_code == 0
    assert camera.is_file()


def test_undo_of_a_run_forgets_its_not_worth_marks(
    cli: CliRunner, locations: Locations
) -> None:
    """Undone, the clip is listed again: the user may have changed the settings."""
    text = locations.config_file.read_text(encoding="utf-8")
    locations.config_file.write_text(text + "[shrink]\nmin_gain_percent = 95\n")
    _shrink(cli, "--apply", "--yes")
    assert not_worth(locations.journal_dir)
    assert run(cli, "undo").exit_code == 0
    assert not not_worth(locations.journal_dir)
    assert "1 video worth lightening" in " ".join(_shrink(cli).output.split())


def test_an_ffmpeg_without_h264_changes_nothing(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refused before anything moves, with the line that updates the image."""
    monkeypatch.setattr(shrink_service, "_encodes", lambda _ffmpeg: False)
    result = run(cli, "shrink", "--apply", "--yes")
    assert result.exit_code == 1
    assert "cannot encode H.264" in result.output
    assert (locations.data_dir / _CAMERA).is_file()
    assert not list(locations.journal_dir.glob("*.jsonl"))


def test_without_an_audit_it_says_to_audit_first(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No index yet: one line, the audit first."""
    point_mounts(locations, monkeypatch)
    result = run(CliRunner(), "shrink")
    assert result.exit_code == 1
    assert "Run 'audit' first" in " ".join(result.output.split())
