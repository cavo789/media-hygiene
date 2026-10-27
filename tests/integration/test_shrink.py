"""`shrink`: the heavy videos listed, lightened, the originals set aside, then undone.

Synthetic clips only, encoded by the test: MJPEG with PCM sound in AVI (an old camera),
and a phone's H.264, never a real video.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.actions import no_overwrite
from media_hygiene.actions import shrink as shrink_actions
from media_hygiene.actions.journal import read_journal
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.not_worth import not_worth
from media_hygiene.services import shrink_tools
from media_hygiene.services.phone_known import PhoneQuery, known_of
from media_hygiene.services.phone_plan import AsideState, PhoneFile
from tests.support.cli import point_mounts, run
from tests.support.runtime import make_runtime
from tests.support.shrink_clips import CAMERA, MTIME, NEEDS_X264, audited

if TYPE_CHECKING:
    from collections.abc import Callable

    from typer.testing import Result

    from media_hygiene.paths.locations import Locations

_MTIME: Final = MTIME
_CAMERA: Final = CAMERA

pytestmark = NEEDS_X264


@pytest.fixture
def cli(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """A camera's MJPEG clip with its sidecar, a phone's H.264, one protected clip."""
    return audited(locations, monkeypatch)


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
    assert "shrink --try" in said
    assert "--apply" in said
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
    """The phone still holds the original: `import --phone` sees it aside, not new."""
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


def test_a_mount_without_atomic_rename_is_lightened_all_the_same(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Docker Desktop refuses renameat2 (EINVAL, seen 2026-10-23): linked instead."""
    monkeypatch.setattr(no_overwrite, "_libc_renameat2", lambda: None)
    camera = locations.data_dir / _CAMERA
    said = " ".join(_shrink(cli, "--apply", "--yes").output.split())
    assert "1 video lightened" in said
    assert "not lightened" not in said
    light = camera.with_suffix(".mp4")
    assert light.is_file()
    assert light.with_name("clip.mp4.xmp").is_file()
    assert not list(light.parent.glob("*.tmp"))


def test_a_move_that_fails_is_said_and_undone(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The original already aside: the run says where both are; undo brings it back."""
    camera = locations.data_dir / _CAMERA

    def refuse(source: Path, target: Path) -> None:
        if target.suffix == ".mp4":
            raise PermissionError(13, "Permission denied")
        source.rename(target)

    monkeypatch.setattr(shrink_actions, "move_no_replace", refuse)
    said = " ".join(_shrink(cli, "--apply", "--yes").output.split())
    assert "'undo' brings it back" in said
    assert "0 videos lightened" in said
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
    monkeypatch.setattr(shrink_tools, "encodes", lambda _ffmpeg: False)
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


def test_a_lighter_video_is_never_proposed_again(
    cli: CliRunner, locations: Locations
) -> None:
    """Even above bits_per_pixel: one more lossy generation would gain little."""
    text = locations.config_file.read_text(encoding="utf-8")
    locations.config_file.write_text(text + "[shrink]\nbits_per_pixel = 0.0001\n")
    _shrink(cli, "--apply", "--yes")
    assert run(cli, "audit").exit_code == 0
    said = " ".join(_shrink(cli).output.split())
    assert "clip.mp4" not in said


def _renamed(light: Path) -> Path:
    """Renamed in the Explorer."""
    return light.rename(light.with_name("renamed.mp4"))


def _moved(light: Path) -> Path:
    """Moved to another folder, as `sort` or the Explorer does."""
    target = light.parent.parent / "Sorted" / "2015" / light.name
    target.parent.mkdir(parents=True)
    return light.rename(target)


def _copied(light: Path) -> Path:
    """Copied elsewhere, its modification time kept (a backup tool)."""
    target = light.parent.parent / "Copy" / light.name
    target.parent.mkdir(parents=True)
    return Path(shutil.copy2(light, target))


def _touched(light: Path) -> Path:
    """Its modification time changed (`touch`)."""
    os.utime(light, ns=(_MTIME * 2, _MTIME * 2))
    return light


def _saved_atomically(light: Path) -> Path:
    """Saved again by a tool writing a new file over it (a new inode)."""
    fresh = light.with_name("fresh.tmp")
    fresh.write_bytes(light.read_bytes())
    fresh.replace(light)
    return light


def _written_in_place(light: Path) -> Path:
    """Written in place: bytes added at its end, its size changed."""
    with light.open("ab") as file:
        file.write(b"\0" * 1024)
    return light


@pytest.mark.parametrize(
    "event",
    [_renamed, _moved, _copied, _touched, _saved_atomically, _written_in_place],
)
def test_a_lighter_video_carries_its_mark_wherever_it_goes(
    cli: CliRunner, locations: Locations, event: Callable[[Path], Path]
) -> None:
    """Journals gone, any bit rate: the mark alone keeps it out of the list (0308)."""
    _shrink(cli, "--apply", "--yes")
    for journal in locations.journal_dir.glob("*.jsonl"):
        journal.unlink()
    now = event((locations.data_dir / _CAMERA).with_suffix(".mp4"))
    text = locations.config_file.read_text(encoding="utf-8")
    locations.config_file.write_text(text + "[shrink]\nbits_per_pixel = 0.0001\n")
    assert run(cli, "audit").exit_code == 0
    said = " ".join(_shrink(cli).output.split())
    assert "phone.mp4" in said  # an H.264 without the mark is listed: the rule bites
    assert now.name not in said
    assert "clip.mp4" not in said


def test_a_lighter_video_at_crf_18_is_never_proposed_again(
    cli: CliRunner, locations: Locations
) -> None:
    """`same_crf = 18` spends more bits; journals gone: the index holds its mark."""
    text = locations.config_file.read_text(encoding="utf-8")
    locations.config_file.write_text(text + "[shrink]\nsame_crf = 18\n")
    _shrink(cli, "--apply", "--yes")
    for journal in locations.journal_dir.glob("*.jsonl"):
        journal.unlink()
    locations.config_file.write_text(
        text + "[shrink]\nsame_crf = 18\nbits_per_pixel = 0.0001\n"
    )
    assert run(cli, "audit").exit_code == 0
    light = (locations.data_dir / _CAMERA).with_suffix(".mp4")
    with closing(sqlite3.connect(locations.index_file)) as index:
        (metadata,) = index.execute(
            "SELECT metadata FROM files WHERE path = ?", (str(light),)
        ).fetchone()
    assert json.loads(metadata)["shrunk"] == "media-hygiene shrink crf=18"
    said = " ".join(_shrink(cli).output.split())
    assert "clip.mp4" not in said
