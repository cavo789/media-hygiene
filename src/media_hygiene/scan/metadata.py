"""What a photo or a video says about itself, recorded for free while it is checked.

Facts only, never judgments: "sharp", "well exposed" or "a good photo" are computed
where they are needed, from these raw measures and configurable thresholds. Everything
is optional: most files hold only a part of it. Stored as JSON in the index, so that a
new field needs no schema change; bump `METADATA_VERSION` when one is added, and the
files already indexed are read again once.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict

METADATA_VERSION: Final = 1


class MediaMetadata(BaseModel):
    """Metadata of one file; dates are kept exactly as written in the file."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    # Where: decimal degrees (south and west negative), metres above sea level.
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    # When, for images: the offset of the EXIF date (`+02:00`), which has none itself.
    offset: str | None = None
    # When, for videos: QuickTime's `creation_time` is UTC; Apple's `creationdate` is
    # local time with its offset. Converting them is the job of whoever sorts.
    created: str | None = None
    created_local: str | None = None
    # With what, and how.
    make: str | None = None
    model: str | None = None
    lens: str | None = None
    focal_length: float | None = None
    exposure_time: float | None = None
    f_number: float | None = None
    iso: int | None = None
    flash: int | None = None
    software: str | None = None
    description: str | None = None
    artist: str | None = None
    # The stars given in Windows (0 to 5): the owner's own judgment.
    rating: int | None = None
    # The file: its format as Pillow names it, the estimated JPEG quality (1 to 100).
    file_format: str | None = None
    jpeg_quality: int | None = None
    # Exposure, on the grayscale thumbnail of the hashes: mean brightness (0 to 255)
    # and the shares of pixels clipped to black and to white (0 to 1).
    brightness: float | None = None
    dark_share: float | None = None
    bright_share: float | None = None
    # Videos, from the container.
    duration: float | None = None
    bit_rate: int | None = None
    codec: str | None = None
    width: int | None = None
    height: int | None = None
    frame_rate: str | None = None
    rotation: int | None = None
    location: str | None = None

    @property
    def recorded_at(self) -> str | None:
        """The date a video was shot, as written: local with its offset when known.

        Returns:
            Apple's local date, else the UTC creation time, else None.
        """
        return self.created_local or self.created

    @property
    def located(self) -> bool:
        """Tell whether the file says where it was taken.

        Returns:
            True when it holds a latitude and a longitude.
        """
        return self.latitude is not None and self.longitude is not None
