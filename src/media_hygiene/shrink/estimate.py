"""How heavy a video will be once lightened: an estimate, said as one.

x264 at CRF 18 spends about `_SAME_BITS` bits per pixel and per frame on a home video,
`_LIGHTER_BITS` at CRF 23 (estimated from the 2026-10-17 proposal: MJPEG 6 to 9 times
smaller; to calibrate with `mh-measure.ps1`); the sound becomes AAC at `AUDIO_RATE`.
Only the encoding tells the real size: a result not worth it is thrown away.
"""

from __future__ import annotations

from typing import Final

AUDIO_RATE: Final = 160_000  # bits per second of AAC
_SAME_BITS: Final = 0.1
_LIGHTER_BITS: Final = 0.07
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
    bits = _SAME_BITS
    short = min(width, height)
    if lines is not None:
        bits = _LIGHTER_BITS
        if short > lines:
            pixels = round(pixels * (lines / short) ** 2)
    per_second = pixels * fps * bits + AUDIO_RATE
    return round(duration * per_second / _BITS_PER_BYTE)
