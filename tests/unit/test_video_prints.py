"""Video fingerprints: a fake `ffmpeg`, the index cache, and the looks compared."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from media_hygiene.constants import BrokenReason, MediaKind
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.video_rows import video_print_of, video_print_row
from media_hygiene.scan import keyframes
from media_hygiene.scan.deps import ScanDeps
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from media_hygiene.scan.video_models import (
    FRAME_POSITIONS,
    VIDEO_PRINT_VERSION,
    FrameHash,
    VideoPrint,
)
from media_hygiene.scan.video_prints import VideoPrinter, look_of

if TYPE_CHECKING:
    from pathlib import Path

PRINT = VideoPrint(tuple(FrameHash(index, 2**64 - 1 - index) for index in range(5)))
METADATA = MediaMetadata(duration=12.0, width=1920, height=1080, codec="h264")


def fake_ffmpeg(tmp_path: Path, body: str) -> str:
    """A shell script standing for `ffmpeg`.

    Args:
        tmp_path: Where to write it.
        body: Its commands.

    Returns:
        Its path.
    """
    script = tmp_path / "ffmpeg"
    script.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    script.chmod(0o755)
    return str(script)


def gradient_ffmpeg(tmp_path: Path) -> str:
    """A fake `ffmpeg` printing a 64 x 64 horizontal gradient, counting its calls."""
    frame = tmp_path / "frame.raw"
    frame.write_bytes(bytes(column * 4 for _ in range(64) for column in range(64)))
    calls = tmp_path / "calls"
    return fake_ffmpeg(tmp_path, f'echo x >> "{calls}"\ncat "{frame}"')


def calls(tmp_path: Path) -> int:
    """How many times the fake `ffmpeg` ran."""
    record = tmp_path / "calls"
    return len(record.read_text().splitlines()) if record.exists() else 0


def test_the_index_columns_round_trip() -> None:
    """A fingerprint, none, a corrupt one or a short one."""
    assert video_print_of(video_print_row(VIDEO_PRINT_VERSION, PRINT)) == (
        VIDEO_PRINT_VERSION,
        PRINT,
    )
    assert video_print_of(video_print_row(VIDEO_PRINT_VERSION, None)) == (1, None)
    assert video_print_of((None, None)) == (0, None)
    assert video_print_of((1, "zz:00")) == (0, None)
    assert video_print_of((1, "00:00")) == (0, None)


def test_a_frame_is_hashed_at_every_position(tmp_path: Path) -> None:
    """One call per position; a gradient has a dHash of ones."""
    ffmpeg = gradient_ffmpeg(tmp_path)
    found = asyncio.run(keyframes.fingerprint(tmp_path / "v.mp4", 10.0, ffmpeg))
    assert found is not None
    assert len(found.frames) == len(FRAME_POSITIONS) == calls(tmp_path)
    assert found.frames[0].dhash == 2**64 - 1


@pytest.mark.parametrize("body", ["echo broken >&2; exit 1", "printf 'short'"])
def test_an_undecodable_video_has_no_fingerprint(tmp_path: Path, body: str) -> None:
    """A codec the executable lacks, or a frame of the wrong size."""
    ffmpeg = fake_ffmpeg(tmp_path, body)
    assert asyncio.run(keyframes.fingerprint(tmp_path / "v.mp4", 10.0, ffmpeg)) is None


def test_a_stuck_decoder_is_stopped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A frame that takes too long gives no fingerprint."""
    monkeypatch.setattr(keyframes, "_TIMEOUT_SECONDS", 0.2)
    ffmpeg = fake_ffmpeg(tmp_path, "exec sleep 5")
    assert asyncio.run(keyframes.fingerprint(tmp_path / "v.mp4", 10.0, ffmpeg)) is None


def test_the_looks_follow_the_rotation() -> None:
    """A portrait phone video is stored landscape with a rotation."""
    facts = FileFacts(metadata=METADATA, video_print=PRINT)
    assert look_of(facts) is not None
    turned = facts.with_metadata(METADATA.model_copy(update={"rotation": -90}))
    look = look_of(turned)
    assert look is not None
    assert (look.width, look.height, look.codec) == (1080, 1920, "h264")
    assert look_of(FileFacts(metadata=METADATA)) is None
    no_size = METADATA.model_copy(update={"width": None})
    assert look_of(FileFacts(metadata=no_size, video_print=PRINT)) is None


def printed(tmp_path: Path, ffmpeg: str | None) -> dict[str, bool]:
    """Run the printer twice on a small library, the second time from the index.

    Args:
        tmp_path: Where the index and the files are.
        ffmpeg: The executable, or None.

    Returns:
        Which file names were described.
    """
    healthy = FileFacts(metadata=METADATA).with_integrity(None, "")
    library = {
        "clip.mp4": healthy,
        "short.mp4": healthy.with_metadata(
            METADATA.model_copy(update={"duration": 0.5})
        ),
        "cut.mp4": healthy.with_integrity(BrokenReason.UNREADABLE_VIDEO, "eof"),
        "photo.jpg": healthy,
    }
    files = [
        MediaFile(
            tmp_path / name,
            1,
            0,
            MediaKind.IMAGE if name.endswith(".jpg") else MediaKind.VIDEO,
        )
        for name in library
    ]
    known = {file.path: library[file.path.name] for file in files}
    looks = {}
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        printer = VideoPrinter(ScanDeps(repository, NullProgress()), ffmpeg)
        for _ in range(2):
            looks = asyncio.run(printer.looks(files, known))
            known = {file.path: repository.get(file) for file in files}
    return {path.name: True for path in looks}


def test_videos_are_fingerprinted_once(tmp_path: Path) -> None:
    """Healthy videos long enough only, and the index spares the second run."""
    assert printed(tmp_path, gradient_ffmpeg(tmp_path)) == {"clip.mp4": True}
    assert calls(tmp_path) == len(FRAME_POSITIONS)


def test_without_ffmpeg_nothing_is_decoded(tmp_path: Path) -> None:
    """No executable: no fingerprint, no error."""
    assert printed(tmp_path, None) == {}
