"""Write the demo library's files: photos with EXIF, copies, videos, broken files."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import pillow_heif
from PIL import Image

from tests.support.docs.pictures import render

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from tests.support.docs.pictures import Picture

CAMERA: Final = ("Canon", "EOS 80D")
PHONE: Final = ("Apple", "iPhone 12")
_MAKE: Final = 0x010F
_MODEL: Final = 0x0110
_EXIF_IFD: Final = 0x8769
_TAKEN_AT: Final = 0x9003
_EXIF_DATE: Final = "%Y:%m:%d %H:%M:%S"
_HEIC: Final = ".heic"
_VIDEO_SECONDS: Final = 8


@dataclass(frozen=True, slots=True)
class Shot:
    """A photo file: its picture, and what the camera wrote with it."""

    picture: Picture
    taken_at: datetime | None
    camera: tuple[str, str] | None = CAMERA
    quality: int = 88
    size: tuple[int, int] | None = None


def stamp(path: Path, when: datetime) -> Path:
    """Set the modification date of a file.

    Args:
        path: The file.
        when: Its new date.

    Returns:
        The same path.
    """
    seconds = when.timestamp()
    os.utime(path, (seconds, seconds))
    return path


def write_shot(path: Path, shot: Shot) -> Path:
    """Write a photo (JPEG, or HEIC after its extension), dated like the camera did.

    Args:
        path: The file to write; its folder is created.
        shot: The picture and its EXIF.

    Returns:
        The file.
    """
    picture = render(shot.picture)
    if shot.size is not None:
        picture = picture.resize(shot.size, Image.Resampling.LANCZOS)
    exif = Image.Exif()
    if shot.camera is not None:
        exif[_MAKE], exif[_MODEL] = shot.camera
    if shot.taken_at is not None:
        exif.get_ifd(_EXIF_IFD)[_TAKEN_AT] = shot.taken_at.strftime(_EXIF_DATE)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.casefold() == _HEIC:
        heic = pillow_heif.from_pillow(picture)
        heic.save(path, quality=shot.quality, exif=exif.tobytes())
    else:
        picture.save(path, "JPEG", quality=shot.quality, exif=exif)
    if shot.taken_at is not None:
        stamp(path, shot.taken_at)
    return path


def copy(source: Path, target: Path, when: datetime) -> Path:
    """Copy the bytes of a file, dated later: a copy made afterwards.

    Args:
        source: The original.
        target: The copy; its folder is created.
        when: The date of the copy.

    Returns:
        The copy.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return stamp(target, when)


def truncate(source: Path, target: Path) -> Path:
    """Write the first half of a file: an interrupted copy.

    Args:
        source: The healthy file.
        target: The broken copy; its folder is created.

    Returns:
        The broken copy.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    target.write_bytes(data[: len(data) // 2])
    return target


def video(path: Path, when: datetime) -> Path:
    """Encode a short video of a Mandelbrot zoom with ffmpeg.

    Args:
        path: The file to write; its folder is created.
        when: Its date.

    Returns:
        The video.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    source = "mandelbrot=size=960x540:rate=25"
    command = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", source]
    command += ["-t", str(_VIDEO_SECONDS), "-pix_fmt", "yuv420p", str(path)]
    subprocess.run(command, check=True)  # noqa: S603 - fixed, trusted arguments
    return stamp(path, when)
