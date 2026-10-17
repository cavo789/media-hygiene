"""`[[classify.place_photos]]` written by the map (TODO 0237): give, take back, follow.

A photo belongs to one place at most; a place renamed on the map renames its entry,
a place deleted takes its photos with it (in the same write); the comments of the file
are kept; the file stays one `ClassifySettings` accepts.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.config.place_photos import HandPhoto, PlacePhotos
from media_hygiene.places.config_file import PlaceEdit, read_places, save_places
from media_hygiene.places.config_photos import (
    give_photos,
    read_place_photos,
    take_back,
)
from media_hygiene.places.renames import renamed

if TYPE_CHECKING:
    from pathlib import Path

GEER = PersonalPlace(name="Geer", latitude=50.66, longitude=5.17)
HOME = PersonalPlace(name="Home", latitude=50.3, longitude=5.1, home=True)
COMMENTED = """# My settings
[classify]
# my own classify comment
target = ''

[[classify.places]]
# grandparents
name = "Geer"
latitude = 50.66
longitude = 5.17

[[classify.places]]
name = "Home"
latitude = 50.3
longitude = 5.1
home = true
"""


def _photo(letter: str, path: str = "C:\\Photos\\2019\\IMG_1.jpg") -> HandPhoto:
    """A photo whose digest is the letter, 64 times."""
    return HandPhoto(sha256=letter * 64, size=10, path=path)


def _settings(config: Path) -> ClassifySettings:
    """`[classify]` of the file, as the next run reads it."""
    return ClassifySettings.model_validate(
        tomllib.loads(config.read_text("utf-8"))["classify"]
    )


def _file(tmp_path: Path) -> Path:
    """The commented file, two places in it."""
    config = tmp_path / "config.toml"
    config.write_text(COMMENTED, "utf-8")
    return config


def test_give_read_back_and_comments_kept(tmp_path: Path) -> None:
    """A literal host path, the size kept, the user's comments untouched."""
    config = _file(tmp_path)
    give_photos(config, PlacePhotos(place="Geer", photos=(_photo("a"), _photo("b"))))
    assert read_place_photos(config) == (
        PlacePhotos(place="Geer", photos=(_photo("a"), _photo("b"))),
    )
    text = config.read_text("utf-8")
    assert text.startswith(COMMENTED)
    assert "path = 'C:\\Photos\\2019\\IMG_1.jpg'" in text
    assert _settings(config).place_photos[0].place == "Geer"


def test_a_photo_given_again_leaves_its_former_place(tmp_path: Path) -> None:
    """One place per photo; an entry left empty goes."""
    config = _file(tmp_path)
    give_photos(config, PlacePhotos(place="Geer", photos=(_photo("a"),)))
    give_photos(config, PlacePhotos(place="Home", photos=(_photo("a"),)))
    assert read_place_photos(config) == (
        PlacePhotos(place="Home", photos=(_photo("a"),)),
    )
    take_back(config, "a" * 64)
    assert not read_place_photos(config)
    assert "place_photos" not in config.read_text("utf-8")


def test_a_place_renamed_or_deleted_takes_its_photos_along(tmp_path: Path) -> None:
    """Renamed: the entry follows; deleted: the entry goes, in the same write."""
    config = _file(tmp_path)
    give_photos(config, PlacePhotos(place="Geer", photos=(_photo("a"),)))
    old = read_places(config)
    edits = [
        PlaceEdit(0, GEER.model_copy(update={"name": "Grandpa"})),
        PlaceEdit(1, HOME),
    ]
    save_places(config, edits, renamed(old, edits))
    assert read_place_photos(config)[0].place == "Grandpa"
    assert _settings(config).places[0].name == "Grandpa"
    old = read_places(config)
    edits = [PlaceEdit(1, HOME)]
    assert renamed(old, edits) == {"Grandpa": None}
    save_places(config, edits, renamed(old, edits))
    assert not read_place_photos(config)
    assert [place.name for place in _settings(config).places] == ["Home"]
    assert "# my own classify comment" in config.read_text("utf-8")
