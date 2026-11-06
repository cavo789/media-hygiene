"""The libraries stay silent: Pillow's palette warning, the ONNX telemetry."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from typing import TYPE_CHECKING

import numpy as np
import pytest
from PIL import Image

from media_hygiene.scan.colour import image_colour
from media_hygiene.scan.rgb import rgb_of

if TYPE_CHECKING:
    from pathlib import Path

_ALPHAS = bytes((0, 128, 255))


def _palette_png() -> bytes:
    """A PNG whose palette has its transparency as a list of bytes."""
    picture = Image.new("P", (4, 4))
    picture.putpalette([255, 0, 0, 0, 255, 0, 0, 0, 255])
    picture.paste(1, (0, 0, 2, 2))
    picture.paste(2, (2, 2, 4, 4))
    buffer = io.BytesIO()
    picture.save(buffer, "PNG", transparency=_ALPHAS)
    return buffer.getvalue()


def test_a_transparent_palette_gives_the_same_pixels_without_a_warning() -> None:
    """`filterwarnings = error` makes a warning fail; the pixels are the direct ones."""
    with Image.open(io.BytesIO(_palette_png())) as picture:
        rgb = rgb_of(picture)
        with pytest.warns(UserWarning, match="Palette images"):
            direct = picture.convert("RGB")
    assert rgb.mode == "RGB"
    assert np.array_equal(np.asarray(rgb), np.asarray(direct))


def test_other_pictures_are_converted_as_usual() -> None:
    """A grey picture has nothing to work around."""
    assert rgb_of(Image.new("L", (2, 2), 7)).getpixel((0, 0)) == (7, 7, 7)


def test_measuring_the_colour_of_such_a_picture_is_silent(tmp_path: Path) -> None:
    """The same files go through the colour measure of the audit."""
    path = tmp_path / "palette.png"
    path.write_bytes(_palette_png())
    assert image_colour(path) is not None


def test_the_runtime_says_nothing_and_its_telemetry_is_off(tmp_path: Path) -> None:
    """Imported our way, with a home it cannot write to: the library stays silent."""
    pytest.importorskip("onnxruntime")
    code = (
        "from media_hygiene.faces.onnx_module import no_telemetry\n"
        "no_telemetry()\nimport onnxruntime\n"
    )
    done = subprocess.run(  # noqa: S603 - this interpreter, a fixed script
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "HOME": str(tmp_path / "missing")},
    )
    assert "telemetry" not in done.stderr
