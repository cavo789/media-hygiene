"""The upright size of a photo, for the outline of a face on the whole picture."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.people.crops import upright_size

if TYPE_CHECKING:
    from pathlib import Path

_ORIENTATION = 0x0112


def test_size_follows_the_exif_turn(tmp_path: Path) -> None:
    """A photo stored 40x20 and turned by 90 degrees is 20x40 for the boxes."""
    flat = tmp_path / "flat.jpg"
    turned = tmp_path / "turned.jpg"
    Image.new("RGB", (40, 20)).save(flat)
    exif = Image.Exif()
    exif[_ORIENTATION] = 6
    Image.new("RGB", (40, 20)).save(turned, exif=exif)
    assert upright_size(flat) == (40, 20)
    assert upright_size(turned) == (20, 40)


def test_size_of_a_missing_or_broken_file_is_none(tmp_path: Path) -> None:
    """No size, so no outline, never an error."""
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"not a picture")
    assert upright_size(broken) is None
    assert upright_size(tmp_path / "gone.jpg") is None
