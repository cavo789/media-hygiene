"""A preview decodes a JPEG at a reduced scale: same size, same orientation (0154)."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import Image

from media_hygiene.report.thumbnails import jpeg_preview, upright_picture

if TYPE_CHECKING:
    from pathlib import Path

_ROTATED: Final = 6  # EXIF: turn 90° to see it upright
_EDGE: Final = 160
_CLOSE: Final = 6.0  # mean difference, in levels out of 255


def photo(path: Path) -> Path:
    """A 1200 x 800 landscape gradient, stored with an EXIF rotation."""
    ramp = np.linspace(0, 255, 1200, dtype=np.float32)
    pixels = np.stack(
        [
            np.tile(ramp, (800, 1)),
            np.tile(ramp[::-1], (800, 1)),
            np.full((800, 1200), 90),
        ],
        axis=-1,
    ).astype(np.uint8)
    exif = Image.Exif()
    exif[0x0112] = _ROTATED
    Image.fromarray(pixels).save(path, "JPEG", quality=92, exif=exif)
    return path


def test_a_drafted_preview_matches_the_full_decode(tmp_path: Path) -> None:
    """Upright (portrait), same size, close to a preview of the whole picture."""
    source = photo(tmp_path / "a.jpg")
    data = jpeg_preview(source, _EDGE)
    assert data is not None
    drafted = Image.open(io.BytesIO(data)).convert("RGB")
    full = upright_picture(source)
    full.thumbnail((_EDGE, _EDGE))
    assert drafted.size == full.size == (107, 160)
    difference = np.abs(
        np.asarray(drafted, dtype=np.float32) - np.asarray(full, dtype=np.float32)
    )
    assert float(difference.mean()) < _CLOSE
