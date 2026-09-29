"""What an image says about itself: EXIF tags, GPS, format, JPEG quality, exposure."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PIL import Image, TiffImagePlugin

from media_hygiene.scan.image_check import (
    inspect_image,
    prepare_image_worker,
    read_image_metadata,
)
from media_hygiene.scan.jpeg_quality import jpeg_quality

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

NICE = (43.0, 41.0, 45.0)
NICE_EAST = (7.0, 15.0, 36.0)


def phone_exif(gps: Mapping[int, object]) -> Image.Exif:
    """The EXIF a phone writes: device, rating, date offset, lens, comment, GPS."""
    exif = Image.Exif()
    exif.update({0x0110: "Pixel 7", 0x4746: 4, 0x0131: "HDR+ 1.0"})
    exif.get_ifd(0x8769).update(
        {
            0x9003: "2023:07:14 18:30:00",
            0x9011: "+02:00",
            0x8827: (125,),
            0xA434: "Pixel 7 back camera",
            0x9286: b"UNICODE\x00" + "Plage de Nice".encode("utf-16-le"),
        }
    )
    exif.get_ifd(0x8825).update(gps)
    return exif


def save(path: Path, exif: Image.Exif, image_format: str = "JPEG") -> Path:
    """Write a small picture with this EXIF."""
    prepare_image_worker()
    picture = Image.new("RGB", (64, 48), (120, 90, 30))
    picture.save(path, image_format, exif=exif.tobytes(), quality=80)
    return path


@pytest.mark.parametrize("image_format", ["JPEG", "HEIF"])
def test_tags_and_position_are_read(tmp_path: Path, image_format: str) -> None:
    """GPS in JPEG and HEIC, the owner's stars, the offset, lens, ISO and comment."""
    gps = {1: "N", 2: NICE, 3: "E", 4: NICE_EAST, 5: b"\x01", 6: 12.5}
    path = save(tmp_path / "shot.img", phone_exif(gps), image_format)
    metadata = inspect_image(path).metadata
    assert metadata is not None
    assert (round(metadata.latitude or 0, 4), metadata.longitude) == (43.6958, 7.26)
    assert metadata.altitude == -12.5  # below sea level
    assert (metadata.rating, metadata.offset, metadata.iso) == (4, "+02:00", 125)
    assert (metadata.lens, metadata.software) == ("Pixel 7 back camera", "HDR+ 1.0")
    assert metadata.description == "Plage de Nice"
    assert metadata.file_format == image_format
    assert metadata.brightness is not None  # measured on the decoded pixels


@pytest.mark.parametrize(
    "gps",
    [
        {},
        {1: "N", 2: (0.0, 0.0, 0.0), 3: "E", 4: (0.0, 0.0, 0.0)},  # no fix
        {1: "N", 2: (95.0, 0.0, 0.0), 3: "E", 4: NICE_EAST},  # out of range
        {1: "S", 2: TiffImagePlugin.IFDRational(43, 0), 3: "W", 4: NICE_EAST},
        {1: "N", 2: NICE},  # no longitude
    ],
    ids=["none", "zero", "out-of-range", "zero-denominator", "half"],
)
def test_impossible_positions_are_ignored(
    tmp_path: Path, gps: dict[int, object]
) -> None:
    """A malformed position is left out; the rest of the metadata stays."""
    metadata = inspect_image(save(tmp_path / "shot.jpg", phone_exif(gps))).metadata
    assert metadata is not None
    assert not metadata.located
    assert metadata.rating == 4


def test_southern_and_western_positions_are_negative(tmp_path: Path) -> None:
    """Hemispheres S and W give negative degrees (written as bytes by some cameras)."""
    gps = {1: b"S", 2: (22.0, 54.0, 0.0), 3: b"W", 4: (43.0, 12.0, 0.0)}
    metadata = inspect_image(save(tmp_path / "rio.jpg", phone_exif(gps))).metadata
    assert metadata is not None
    assert (metadata.latitude, metadata.longitude) == (-22.9, -43.2)


def test_the_header_alone_gives_the_same_tags(tmp_path: Path) -> None:
    """The one-time reading of older images needs no decode, and has no exposure."""
    path = save(
        tmp_path / "shot.jpg", phone_exif({1: "N", 2: NICE, 3: "E", 4: NICE_EAST})
    )
    header = read_image_metadata(path)
    decoded = inspect_image(path).metadata
    assert decoded is not None
    unmeasured = {"brightness": None, "dark_share": None, "bright_share": None}
    assert header == decoded.model_copy(update=unmeasured)
    assert read_image_metadata(tmp_path / "missing.jpg") is None


@pytest.mark.parametrize("quality", [30, 75, 95])
def test_jpeg_quality_is_estimated(tmp_path: Path, quality: int) -> None:
    """The IJG quality comes back from the luminance table."""
    path = tmp_path / "q.jpg"
    Image.radial_gradient("L").save(path, quality=quality)
    with Image.open(path) as image:
        assert jpeg_quality(image) == quality


@pytest.mark.parametrize(
    ("color", "field"),
    [(0, "dark_share"), (255, "bright_share")],
    ids=["black", "white"],
)
def test_exposure_counts_clipped_pixels(tmp_path: Path, color: int, field: str) -> None:
    """A black frame is all clipped to black, a white one all to white."""
    path = tmp_path / "flat.png"
    Image.new("L", (40, 30), color).save(path)
    metadata = inspect_image(path).metadata
    assert metadata is not None
    assert getattr(metadata, field) == 1.0
    assert metadata.brightness == float(color)
    assert metadata.jpeg_quality is None
