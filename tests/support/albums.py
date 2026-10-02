r"""The sorting library, classified, ready for albums under `C:\\Photos\\Albums`."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Final

from PIL import Image

from tests.support.cli import run
from tests.support.sorting import PHOTOS, build_library

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

ALBUMS: Final = f"{PHOTOS}/Albums"
WEDDING_CATEGORY: Final = "Mariage"
_RATING_TAG: Final = 0x4746


def rate(path: Path, stars: int) -> None:
    """Give a photo stars, as Windows writes them in its EXIF.

    Args:
        path: The photo.
        stars: 0 to 5.
    """
    with Image.open(path) as picture:
        exif = picture.getexif()
        exif[_RATING_TAG] = stars
        picture.save(path, "JPEG", quality=92, exif=exif)


def classified(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """The library alone, a few photos rated, classified; the albums root set.

    Args:
        cli: The runner.
        locations: The test mount points.
        monkeypatch: Sets `[album] root` through the environment.

    Returns:
        The folder of the photos.
    """
    shutil.rmtree(locations.data_dir)
    build_library(locations.data_dir)
    photos = locations.data_dir / PHOTOS
    rate(photos / "Mariage" / "DSC_0001.jpg", 4)
    rate(photos / "Divers" / "IMG_9000.jpg", 5)
    rate(photos / "Mariage" / "DSC_0002.jpg", 2)
    monkeypatch.setenv("MEDIA_HYGIENE_ALBUM__ROOT", "C:\\Photos\\Albums")
    assert run(cli, "classify").exit_code == 0
    return photos


def album_files(locations: Locations, name: str) -> dict[str, Path]:
    """The files of an album, its marker apart.

    Args:
        locations: The test mount points.
        name: The album.

    Returns:
        Name → path.
    """
    folder = locations.data_dir / ALBUMS / name
    return {
        path.name: path
        for path in folder.iterdir()
        if path.is_file() and not path.name.startswith(".")
    }
