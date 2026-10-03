"""What a video looks like: perceptual hashes of a few frames, its length and size.

A re-encoded copy (shared by a messaging app, converted, recompressed) is not identical
to its original, but the same frames, at the same moments, still hash alike.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Moments of the frames hashed, as shares of the duration: never the very first or
# last frame, often black or a fade.
FRAME_POSITIONS: Final = (0.1, 0.3, 0.5, 0.7, 0.9)
# Bump when the frames or their hashing change: every video is fingerprinted again once.
VIDEO_PRINT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class FrameHash:
    """The 64-bit dHash and pHash of one frame, as for images."""

    dhash: int
    phash: int


@dataclass(frozen=True, slots=True)
class VideoPrint:
    """The hashes of the frames at `FRAME_POSITIONS`, in that order."""

    frames: tuple[FrameHash, ...]


@dataclass(frozen=True, slots=True)
class VideoLook:
    """A video as near-duplicate detection compares it, with what the report shows.

    `width` and `height` are the displayed size (rotation applied).
    """

    print: VideoPrint
    duration: float
    width: int
    height: int
    recorded_at: str | None = None
    codec: str | None = None

    @property
    def pixels(self) -> int:
        """Displayed resolution, in pixels.

        Returns:
            Width times height.
        """
        return self.width * self.height
