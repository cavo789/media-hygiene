"""What a rule reads of one file: its kind, its host path, its camera.

Only names and metadata: the vision model is unreliable for documents and received
pictures (0029). A screenshot has no camera and a telling name, a PNG format or a tiny
size; a picture received through a messaging app has lost its EXIF and carries the
app's name; a downloaded film or series carries a season, a resolution or a codec.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.dating import has_camera_trace
from media_hygiene.classify.rules.kinds import FileKind
from media_hygiene.constants import VIDEO_EXTENSIONS

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput

type Test = Callable[[MediaInput], bool]

_SCREENSHOT_NAMES: Final = re.compile(
    r"screen[ _-]?shot|capture[ _-]d.?[ée]cran|schermafbeelding|bildschirmfoto"
    r"|^scr(?:een)?[_-]?\d",
    re.IGNORECASE,
)
_RECEIVED_NAMES: Final = re.compile(
    r"^(?:IMG|VID)-\d{8}-WA\d+|^received_\d+|^signal-\d{4}-\d{2}-\d{2}"
    r"|^photo_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}",
    re.IGNORECASE,
)
# A tag of a release name, between separators: `Show.S01E05.1080p.x264-GROUP`.
_DOWNLOAD_NAMES: Final = re.compile(
    r"(?<![a-z0-9])(?:s\d{1,2}e\d{1,3}|(?:480|576|720|1080|2160)[pi]|[xh]26[45]"
    r"|hevc|xvid|divx|web-?dl|web-?rip|blu-?ray|[bh]d-?rip|dvd-?rip|hdtv)(?![a-z0-9])",
    re.IGNORECASE,
)
_PNG: Final = ".png"
TINY_SIDE: Final = 400  # pixels: icons, stickers, thumbnails


def is_screenshot(file: MediaInput) -> bool:
    """Tell a screenshot, a document or a tiny image: never from a camera.

    Args:
        file: The file.

    Returns:
        True for a screenshot name, or a PNG or tiny image without a camera trace.
    """
    if _SCREENSHOT_NAMES.search(file.path.stem):
        return True
    if has_camera_trace(file):
        return False
    visual = file.visual
    tiny = visual is not None and 0 < max(visual.width, visual.height) < TINY_SIDE
    return tiny or file.path.suffix.casefold() == _PNG


def is_received(file: MediaInput) -> bool:
    """Tell a picture received through a messaging app: its name, no EXIF.

    Args:
        file: The file.

    Returns:
        True when the name is a messaging app's and no camera wrote a date.
    """
    return file.taken_at is None and bool(_RECEIVED_NAMES.search(file.path.stem))


def is_download(file: MediaInput) -> bool:
    """Tell a downloaded film or series: a video whose name says so.

    Args:
        file: The file.

    Returns:
        True for a video named with a season, a resolution or a codec.
    """
    return file.path.suffix.casefold() in VIDEO_EXTENSIONS and bool(
        _DOWNLOAD_NAMES.search(file.path.stem)
    )


KIND_TESTS: Final[dict[FileKind, Test]] = {
    FileKind.SCREENSHOT: is_screenshot,
    FileKind.RECEIVED: is_received,
    FileKind.DOWNLOAD: is_download,
}


def path_test(pattern: str, host: Callable[[Path], str]) -> Test:
    """A test searching a regular expression in the host path of a file.

    Args:
        pattern: The rule's `pattern`, e.g. `(?i)kermesse`.
        host: Container path → host path.

    Returns:
        The test: folders and file name, as the user's computer writes them.
    """
    compiled = re.compile(pattern)
    return lambda file: bool(compiled.search(host(file.path)))


def camera_test(pattern: str) -> Test:
    """A test searching a regular expression in the make and model of a file.

    Args:
        pattern: The rule's `pattern`, e.g. `(?i)dji`.

    Returns:
        The test: false for a file without a make nor a model.
    """
    compiled = re.compile(pattern)

    def test(file: MediaInput) -> bool:
        """Search the make and model of one file.

        Args:
            file: The file.

        Returns:
            True when the pattern is found.
        """
        metadata = file.metadata
        names = (
            (file.camera, metadata.make, metadata.model) if metadata else (file.camera,)
        )
        return bool(compiled.search(" ".join(name for name in names if name)))

    return test
