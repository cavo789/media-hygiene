"""0841: a face found on the turned picture is placed back on the upright one."""

from __future__ import annotations

import pytest
from PIL import Image, ImageDraw

from media_hygiene.faces.models import FaceBox
from media_hygiene.person.second_look import Turn, upright_box

_SQUARE = (300, 50, 340, 90)  # its centre: (320, 70)


@pytest.mark.parametrize("angle", [0, 15, -30, 45, 90, -90])
def test_the_box_found_turned_lies_on_the_same_spot_upright(angle: int) -> None:
    """A white square, turned: its box placed back has the square's centre."""
    picture = Image.new("L", (400, 300), 0)
    ImageDraw.Draw(picture).rectangle(_SQUARE, fill=255)
    turned = picture.rotate(angle, expand=True)
    left, top, right, bottom = turned.getbbox() or (0, 0, 0, 0)
    found = FaceBox(left, top, right - left, bottom - top)
    box = upright_box(found, Turn(angle, picture.size, turned.size))
    assert box.x + box.width / 2 == pytest.approx(320, abs=2)
    assert box.y + box.height / 2 == pytest.approx(70, abs=2)
