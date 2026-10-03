"""Store the fingerprint of a video in its row of the index, and read it back.

The column holds one `dhash:phash` pair per frame, in hexadecimal (SQLite integers are
signed), separated by commas. NULL with a version: fingerprinted, nothing decodable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.scan.video_models import FRAME_POSITIONS, FrameHash, VideoPrint

if TYPE_CHECKING:
    from collections.abc import Sequence

_FRAMES: Final = ","
_HASHES: Final = ":"
_HEX: Final = 16


def video_print_row(version: int, video_print: VideoPrint | None) -> tuple[object, ...]:
    """Flatten a fingerprint into the version 5 columns.

    Args:
        version: The fingerprint version (0: never fingerprinted).
        video_print: The fingerprint, or None.

    Returns:
        video_print_version, video_print.
    """
    if video_print is None:
        return version, None
    text = _FRAMES.join(
        f"{frame.dhash:016x}{_HASHES}{frame.phash:016x}" for frame in video_print.frames
    )
    return version, text


def video_print_of(values: Sequence[object]) -> tuple[int, VideoPrint | None]:
    """Rebuild a fingerprint from the version 5 columns.

    Args:
        values: video_print_version, video_print.

    Returns:
        The version and the fingerprint. A corrupt fingerprint reads as never made.
    """
    version, text = values
    if not isinstance(version, int):
        return 0, None
    if not isinstance(text, str):
        return version, None
    try:
        frames = tuple(_frame(item) for item in text.split(_FRAMES))
    except ValueError:
        return 0, None
    if len(frames) != len(FRAME_POSITIONS):
        return 0, None
    return version, VideoPrint(frames)


def _frame(text: str) -> FrameHash:
    """Read the hashes of one frame.

    Args:
        text: `dhash:phash` in hexadecimal.

    Returns:
        The hashes.

    Raises:
        ValueError: The text is not two hexadecimal numbers.
    """
    first, second = text.split(_HASHES)
    return FrameHash(int(first, _HEX), int(second, _HEX))
