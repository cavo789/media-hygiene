"""`[places] reverse_lookup` switched on the map page (0536)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config.places_settings import PlacesSettings
from media_hygiene.places.lookup_switch import LookupAsked, lookup_of, save_lookup

if TYPE_CHECKING:
    from pathlib import Path


def test_missing_or_odd_values_read_as_ask(tmp_path: Path) -> None:
    """No file, a bad file or an unknown value: the default, ask."""
    config = tmp_path / "config.toml"
    assert lookup_of(config) == "ask"
    config.write_text("[places]\nreverse_lookup = 'maybe'\n", "utf-8")
    assert lookup_of(config) == "ask"
    config.write_text("[places\n", "utf-8")
    assert lookup_of(config) == "ask"


def test_a_choice_is_written_with_the_comments_and_read_back(tmp_path: Path) -> None:
    """The file keeps its comments; the settings read the same value."""
    config = tmp_path / "config.toml"
    config.write_text("# mine\n[places]\ntiles = 'x'\n", "utf-8")
    assert save_lookup(config, LookupAsked(lookup="never")) == "never"
    text = config.read_text("utf-8")
    assert text.startswith("# mine")
    assert "tiles = 'x'" in text
    assert lookup_of(config) == "never"
    assert (
        PlacesSettings.model_validate({"reverse_lookup": "never"}).reverse_lookup
        == "never"
    )
