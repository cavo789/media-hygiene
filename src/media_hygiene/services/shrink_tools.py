"""The `ffmpeg` and `ffprobe` that `shrink` encodes with: one able to write H.264."""

from __future__ import annotations

import shutil
import subprocess  # a fixed command: ffmpeg's list of encoders
from typing import Final

from media_hygiene.constants import FFMPEG_BINARY, FFPROBE_BINARY
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.shrink.check import Tools

_ENCODER: Final = "libx264"
_ENCODERS_SECONDS: Final = 30


def encoding_tools() -> Tools:
    """Find the tools, refusing an `ffmpeg` that cannot encode H.264.

    Returns:
        The `ffmpeg` and `ffprobe` to use.

    Raises:
        MountError: No `ffmpeg` able to encode H.264.
    """
    ffmpeg, ffprobe = shutil.which(FFMPEG_BINARY), shutil.which(FFPROBE_BINARY)
    if ffmpeg is None or ffprobe is None or not encodes(ffmpeg):
        raise MountError(
            _("This ffmpeg cannot encode H.264: nothing was changed."),
            _("Update the image: mh update."),
        )
    return Tools(ffmpeg, ffprobe)


def encodes(ffmpeg: str) -> bool:
    """Tell whether an `ffmpeg` can encode H.264 (the image's, since 0303).

    Args:
        ffmpeg: The executable.

    Returns:
        True when it lists `libx264` among its encoders.
    """
    try:
        listed = subprocess.run(  # noqa: S603  # a fixed command, no user input
            (ffmpeg, "-hide_banner", "-encoders"),
            capture_output=True,
            check=False,
            timeout=_ENCODERS_SECONDS,
        )
    except OSError, subprocess.TimeoutExpired:
        return False
    return _ENCODER in listed.stdout.decode(errors="replace")
