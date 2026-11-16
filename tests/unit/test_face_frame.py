"""Each face's box as fractions of its upright photo, for the large view (0838)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from PIL import Image

from media_hygiene.faces.models import FaceBox
from media_hygiene.person.face_frame import box_fractions, upright_size

_TEMPLATES = Path("src/media_hygiene/review/templates")
_ORIENTATION = 0x0112
_TURNED = 6


def test_a_box_becomes_fractions_of_the_picture() -> None:
    """A 100 by 50 box at (200, 100) of an 800 by 400 picture."""
    fractions = box_fractions(FaceBox(200, 100, 100, 50), (800, 400))
    assert fractions == {"x": 0.25, "y": 0.25, "w": 0.125, "h": 0.125}


def test_a_box_over_the_edge_stays_inside() -> None:
    """A detector's box a little out of the picture is clamped."""
    fractions = box_fractions(FaceBox(-10, 390, 900, 50), (800, 400))
    assert fractions == {"x": 0.0, "y": 0.975, "w": 1.0, "h": 0.125}


def test_the_size_comes_from_the_index(tmp_path: Path) -> None:
    """The index's upright width and height win over the file."""
    index = tmp_path / "index.sqlite"
    with sqlite3.connect(index) as connection:
        connection.execute(
            "CREATE TABLE files (path TEXT, width INTEGER, height INTEGER)"
        )
        connection.execute(
            "INSERT INTO files VALUES (?, ?, ?)", ("/data/x.jpg", 30, 40)
        )
    connection.close()
    assert upright_size(index, Path("/data/x.jpg")) == (30, 40)


@pytest.mark.parametrize(("turned", "expected"), [(False, (60, 20)), (True, (20, 60))])
def test_without_the_index_the_header_gives_it_upright(
    tmp_path: Path, *, turned: bool, expected: tuple[int, int]
) -> None:
    """A photo lying on its side (EXIF 6) gives its upright size."""
    photo = tmp_path / "x.jpg"
    exif = Image.Exif()
    if turned:
        exif[_ORIENTATION] = _TURNED
    Image.new("RGB", (60, 20)).save(photo, exif=exif)
    assert upright_size(None, photo) == expected
    assert upright_size(tmp_path / "missing.sqlite", tmp_path / "nope.jpg") is None


def test_the_large_view_draws_the_boxes_and_the_name_switch() -> None:
    """The shared who line includes the boxes; the view carries the switch's words."""
    who = (_TEMPLATES / "pick_who.js.j2").read_text(encoding="utf-8")
    assert '{% include "pick_who_boxes.js.j2" %}' in who
    boxes = (_TEMPLATES / "pick_who_boxes.js.j2").read_text(encoding="utf-8")
    assert "localStorage" in boxes
    assert "try {" in boxes
    view = (_TEMPLATES / "pick_viewer.html.j2").read_text(encoding="utf-8")
    assert "data-show=" in view
    assert "data-hide=" in view
    combo = (_TEMPLATES / "combo_list.js.j2").read_text(encoding="utf-8")
    assert 'classList.toggle("above"' in combo
