"""`places` writes `[[classify.places]]` into a commented `config.toml`."""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.config.loader import write_default_config
from media_hygiene.constants import Locale
from media_hygiene.places.config_file import PlaceEdit, read_places, save_places

if TYPE_CHECKING:
    from pathlib import Path

HOME = PersonalPlace(name="Home", latitude=50.3, longitude=5.1, radius_m=150, home=True)
SHED = PersonalPlace(name="Shed", latitude=50.2, longitude=5.2, radius_m=50.5)
HAND_WRITTEN = """\
# My own settings
[classify]
sure = 80  # the threshold

# The places I wrote myself
[[classify.places]]
name = "Home"  # where we live
latitude = 50.0
longitude = 5.0
home = true

[[classify.places]]
name = "Old shed"
latitude = 50.1
longitude = 5.1

[[classify.rules]]
name = "Existing folders"
match = "existing_folder"
"""


def test_a_place_is_added_to_the_generated_file_without_losing_a_comment(
    tmp_path: Path,
) -> None:
    """Every line of the generated file is still there, the place at the end."""
    config = tmp_path / "config.toml"
    write_default_config(config, Locale.EN)
    before = config.read_text("utf-8")
    save_places(config, [PlaceEdit(None, HOME)])
    after = config.read_text("utf-8")
    assert after.startswith(before.rstrip())
    assert read_places(config) == (HOME,)
    assert tomllib.loads(after)["classify"]["rules"]


def test_places_are_edited_in_place_keeping_their_comments(tmp_path: Path) -> None:
    """Home moves, the old shed goes, a new shed follows home."""
    config = tmp_path / "config.toml"
    config.write_text(HAND_WRITTEN, "utf-8")
    save_places(config, [PlaceEdit(0, HOME), PlaceEdit(None, SHED)])
    text = config.read_text("utf-8")
    assert "# My own settings" in text
    assert "# The places I wrote myself" in text
    assert 'name = "Home"  # where we live' in text
    assert "Old shed" not in text
    assert read_places(config) == (HOME, SHED)
    assert text.index('"Shed"') < text.index("[[classify.rules]]")


def test_a_place_no_longer_home_loses_its_flag(tmp_path: Path) -> None:
    """`home = false` is not written: the line goes."""
    config = tmp_path / "config.toml"
    config.write_text(HAND_WRITTEN, "utf-8")
    moved = HOME.model_copy(update={"home": False})
    save_places(config, [PlaceEdit(0, moved), PlaceEdit(1, SHED)])
    assert read_places(config) == (moved, SHED)
    assert "home" not in config.read_text("utf-8").split("[[classify.rules]]")[0][-200:]


def test_removing_every_place_removes_the_array(tmp_path: Path) -> None:
    """No empty `places` key is left behind."""
    config = tmp_path / "config.toml"
    config.write_text(HAND_WRITTEN, "utf-8")
    save_places(config, [])
    assert not read_places(config)
    assert "[[classify.places]]" not in config.read_text("utf-8")


def test_an_inline_array_is_written_again_as_tables(tmp_path: Path) -> None:
    """`places = [{...}]` becomes `[[classify.places]]`."""
    config = tmp_path / "config.toml"
    config.write_text(
        '[classify]\nplaces = [{name = "X", latitude = 1, longitude = 2}]\n', "utf-8"
    )
    save_places(config, [PlaceEdit(0, SHED)])
    assert read_places(config) == (SHED,)
    assert "[[classify.places]]" in config.read_text("utf-8")


def test_a_missing_file_is_created(tmp_path: Path) -> None:
    """Nothing to keep: the places alone."""
    config = tmp_path / "config.toml"
    assert not read_places(config)
    save_places(config, [PlaceEdit(None, SHED)])
    assert read_places(config) == (SHED,)


def test_two_places_of_one_name_are_refused(tmp_path: Path) -> None:
    """The file is not touched."""
    config = tmp_path / "config.toml"
    config.write_text(HAND_WRITTEN, "utf-8")
    with pytest.raises(ValueError, match="two places"):
        save_places(config, [PlaceEdit(None, SHED), PlaceEdit(None, SHED)])
    assert config.read_text("utf-8") == HAND_WRITTEN
