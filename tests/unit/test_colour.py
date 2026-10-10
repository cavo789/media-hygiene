"""Colourfulness: black and white versus colour, and when two versions differ."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from media_hygiene.plan.likeness import same_colours
from media_hygiene.scan.colour import colourfulness, image_colour

if TYPE_CHECKING:
    from pathlib import Path


def stripes(path: Path, *, grey: bool) -> Path:
    """Red, green and blue stripes, or the same in grey."""
    pixels = np.zeros((64, 96, 3), dtype=np.uint8)
    for index in range(3):
        pixels[:, index * 32 : (index + 1) * 32, index] = 220
    image = Image.fromarray(pixels)
    if grey:
        image = image.convert("L").convert("RGB")
    image.save(path)
    return path


def test_grey_has_no_colour(tmp_path: Path) -> None:
    """About 0 for grey, far more for vivid stripes; an unreadable file: unknown."""
    grey = image_colour(stripes(tmp_path / "grey.png", grey=True))
    vivid = image_colour(stripes(tmp_path / "vivid.png", grey=False))
    assert grey is not None
    assert vivid is not None
    assert grey < 1
    assert vivid > 50
    (tmp_path / "broken.jpg").write_bytes(b"not a picture")
    assert image_colour(tmp_path / "broken.jpg") is None
    flat = np.full((8, 8, 3), 128, dtype=np.uint8)
    assert colourfulness(flat) == 0


def test_same_colours() -> None:
    """Only a clearly colourful version against one with less than half of it."""
    assert not same_colours(1.5, 37.9)  # the black and white edit of a video
    assert same_colours(30.0, 37.9)  # recompressed: a little less colour
    assert same_colours(2.0, 8.0)  # both dull
    assert same_colours(None, 37.9)  # unknown: no reason to separate them
