"""A photo made ready to send (0296): upright, fitted, its GPS position removed.

Each copy is read back with Pillow: its size, its orientation, what its EXIF keeps.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Final

from PIL import ExifTags, Image

from media_hygiene.share.sent_photo import SendJob, sent_jpeg

if TYPE_CHECKING:
    from pathlib import Path

_MODEL: Final = 0x0110
_DESCRIPTION: Final = 0x010E
_ORIENTATION: Final = 0x0112
_TAKEN: Final = 0x9003
_MAKER_NOTE: Final = 0x927C
_ROTATED: Final = 6  # turned 90 degrees: stored landscape, shown portrait


def gps_photo(path: Path, *, orientation: int = _ROTATED) -> Path:
    """A 4000 x 3000 JPEG taken in Crete: GPS, date, camera, maker notes, XMP."""
    exif = Image.Exif()
    exif[_MODEL] = "Pixel 7"
    exif[_DESCRIPTION] = "Knossos"
    exif[_ORIENTATION] = orientation
    exif.get_ifd(ExifTags.IFD.Exif).update({_TAKEN: "2023:07:01 10:00:00"})
    exif.get_ifd(ExifTags.IFD.Exif)[_MAKER_NOTE] = b"serial 1234"
    exif.get_ifd(ExifTags.IFD.GPSInfo).update({1: "N", 2: (35.0, 17.0, 54.0)})
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (4000, 3000), (180, 40, 40)).save(
        path, exif=exif.tobytes(), xmp=b"<x:xmpmeta>35.29 N</x:xmpmeta>"
    )
    return path


def _read(data: bytes | None) -> Image.Image:
    """The copy, opened."""
    assert data is not None
    return Image.open(io.BytesIO(data))


def test_the_copy_is_upright_fitted_and_without_gps(tmp_path: Path) -> None:
    """GPS, maker notes and XMP gone; the date, the camera, the description kept."""
    copy = _read(sent_jpeg(SendJob(2048, 85), gps_photo(tmp_path / "IMG_1.jpg")))
    assert copy.format == "JPEG"
    assert copy.size == (1536, 2048)  # turned upright, its long side 2048
    exif = copy.getexif()
    assert exif[_ORIENTATION] == 1
    assert exif[_MODEL] == "Pixel 7"
    assert exif[_DESCRIPTION] == "Knossos"
    assert exif.get_ifd(ExifTags.IFD.Exif)[_TAKEN] == "2023:07:01 10:00:00"
    assert _MAKER_NOTE not in exif.get_ifd(ExifTags.IFD.Exif)
    assert ExifTags.IFD.GPSInfo not in exif
    assert not exif.get_ifd(ExifTags.IFD.GPSInfo)
    assert "xmp" not in copy.info


def test_the_gps_position_stays_when_asked(tmp_path: Path) -> None:
    """`--keep-gps`: the position read back as it was."""
    job = SendJob(1024, 85, keep_gps=True)
    copy = _read(sent_jpeg(job, gps_photo(tmp_path / "IMG_1.jpg", orientation=1)))
    assert copy.size == (1024, 768)
    gps = copy.getexif().get_ifd(ExifTags.IFD.GPSInfo)
    assert gps[1] == "N"
    assert tuple(float(part) for part in gps[2]) == (35.0, 17.0, 54.0)


def test_a_small_photo_is_never_enlarged_and_without_exif_has_none(
    tmp_path: Path,
) -> None:
    """A 800 x 600 photo stays so; no EXIF in, none out."""
    source = tmp_path / "small.png"
    Image.new("RGB", (800, 600), (1, 2, 3)).save(source)
    copy = _read(sent_jpeg(SendJob(2048, 85), source))
    assert copy.size == (800, 600)
    assert not copy.getexif()


def test_a_damaged_photo_gives_nothing(tmp_path: Path) -> None:
    """Not a picture: None, counted by the caller as not read."""
    source = tmp_path / "broken.jpg"
    source.write_bytes(b"not a jpeg")
    assert sent_jpeg(SendJob(2048, 85), source) is None
