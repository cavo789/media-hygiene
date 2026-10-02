"""A place drawn from an OpenStreetMap area: saved, read back, matching its photos."""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.models import SortReason
from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.config.loader import write_default_config
from media_hygiene.constants import Locale
from media_hygiene.places.config_file import PlaceEdit, read_places, save_places
from tests.support.located import PLACE_RULE, located, start_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.geo.areas import Shape

# A fictitious village shaped like a diamond, with a pond (a hole) in its east half.
DIAMOND: Final[Shape] = (
    (
        ((50.6, 5.0), (50.7, 5.1), (50.6, 5.2), (50.5, 5.1)),
        ((50.59, 5.14), (50.61, 5.14), (50.61, 5.16), (50.59, 5.16)),
    ),
)
VILLAGE: Final = PersonalPlace(
    name="Fictiville", latitude=50.6, longitude=5.1, osm="R9000001", area=DIAMOND
)
INSIDE: Final = (50.62, 5.08)
CORNER: Final = (50.69, 5.01)  # in the box, outside the diamond
POND: Final = (50.6, 5.15)


def test_an_area_survives_a_commented_config_file(tmp_path: Path) -> None:
    """Every comment kept; the area, its id and its middle read back as written."""
    config = tmp_path / "config.toml"
    write_default_config(config, Locale.EN)
    comments = [line for line in config.read_text("utf-8").splitlines() if "#" in line]
    save_places(config, [PlaceEdit(None, VILLAGE)])
    text = config.read_text("utf-8")
    assert all(line in text for line in comments)
    assert read_places(config) == (VILLAGE,)
    written = tomllib.loads(text)["classify"]["places"][0]
    assert written["osm"] == "R9000001"
    assert "radius_m" not in written
    # Saved again as a circle: the area and its id go away.
    circle = VILLAGE.model_copy(update={"area": None, "osm": "", "radius_m": 500})
    save_places(config, [PlaceEdit(0, circle)])
    assert read_places(config) == (circle,)
    assert "area = [" not in config.read_text("utf-8")


def test_the_photos_inside_the_area_take_its_name(tmp_path: Path) -> None:
    """Inside: the village; in the box's corner or in the pond: not."""
    config = tmp_path / "config.toml"
    save_places(config, [PlaceEdit(None, VILLAGE)])
    places = read_places(config)
    files = [
        located("inside.jpg", start_of(1), INSIDE),
        located("corner.jpg", start_of(5), CORNER),
        located("pond.jpg", start_of(9), POND),
    ]
    settings = ClassifySettings(rules=(PLACE_RULE,), places=places)
    found = {
        proposal.file.path.name: proposal
        for proposal in classify(files, settings, Scope()).proposals
    }
    assert found["inside.jpg"].reason is SortReason.PLACE
    assert found["inside.jpg"].folder == "2023/Fictiville"
    assert found["corner.jpg"].reason is not SortReason.PLACE
    assert found["pond.jpg"].reason is not SortReason.PLACE
