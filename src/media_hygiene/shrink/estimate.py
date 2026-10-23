"""How heavy a video will be once lightened: an estimate, said as one.

x264 at CRF 23, both levels' default, spends about `_BITS` bits per pixel and per frame
on a home video (measured 2026-10-23, `mh-measure.ps1` step 34: two MJPEG 1280x720
clips of a Panasonic camera, 26 % and 29 % of their size, assuming 30 frames per
second; at CRF 18, about 0.55 and 66 to 69 %); `--lighter` only shrinks the picture
besides. The sound becomes AAC at `AUDIO_RATE`.
Only the encoding tells the real size: a result not worth it is thrown away.
"""

from __future__ import annotations

from typing import Final

AUDIO_RATE: Final = 160_000  # bits per second of AAC
_BITS: Final = 0.22
_BITS_PER_BYTE: Final = 8


def estimated_size(
    duration: float, picture: tuple[int, int, float], lines: int | None
) -> int:
    """Estimate the size of a video once re-encoded.

    Args:
        duration: Its length, in seconds.
        picture: Its width, height and frames per second.
        lines: At most this many lines on its short side (`--lighter`), or None to
            keep its size.

    Returns:
        The bytes, estimated.
    """
    width, height, fps = picture
    pixels = width * height
    short = min(width, height)
    if lines is not None and short > lines:
        pixels = round(pixels * (lines / short) ** 2)
    per_second = pixels * fps * _BITS + AUDIO_RATE
    return round(duration * per_second / _BITS_PER_BYTE)
