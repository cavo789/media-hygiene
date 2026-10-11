"""A refused item of an array of tables is named by its `name`, next to its number."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.origin import Origin, item_name
from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from tests.unit.test_config_errors import refused

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations

_NO_MATCH = '[[classify.rules]]\nname = "Birthday"\ncategory = "Parties"\n'


@pytest.fixture(autouse=True)
def _english() -> Iterator[None]:
    """Each test starts in English and leaves the default language behind.

    Yields:
        Control to the test.
    """
    install(Locale.EN)
    yield
    install(Locale.EN)


def test_a_named_rule_is_named(locations: Locations) -> None:
    """Pydantic's own error gets the name of the rule, the number is kept."""
    locations.config_file.write_text(_NO_MATCH)
    assert refused(locations).message == (
        "'match' in [[classify.rules]] number 1 ('Birthday') of config.toml: "
        "this setting is required."
    )


def test_a_named_rule_reads_in_french(locations: Locations) -> None:
    """French quotes the name with guillemets."""
    locations.config_file.write_text(_NO_MATCH)
    install(Locale.FR)
    assert "[[classify.rules]] n° 1 (« Birthday ») de config.toml" in (
        refused(locations).message
    )


def test_an_unnamed_rule_keeps_its_number_alone(locations: Locations) -> None:
    """Without a name, or with a name that is no text, the number is enough."""
    locations.config_file.write_text(
        '[[classify.rules]]\ncategory = "A"\n[[classify.rules]]\nname = 3\n'
    )
    message = refused(locations).message
    assert "'match' in [[classify.rules]] number 1 of config.toml" in message
    assert "'name' in [[classify.rules]] number 2 of config.toml: a text" in message


def test_a_reason_naming_the_item_is_not_repeated(locations: Locations) -> None:
    """The project's validator already names the rule: said once, not twice."""
    locations.config_file.write_text(
        '[[classify.rules]]\nname = "Birthday"\nmatch = "calendar"\n'
        'dates = "02-30"\ncategory = "Parties"\n'
    )
    message = refused(locations).message
    assert message.startswith(
        "[[classify.rules]] number 1 in config.toml: rule 'Birthday'"
    )
    assert message.count("Birthday") == 1


def test_a_refused_name_is_not_repeated(locations: Locations) -> None:
    """A place whose name is the refused value: the reason quotes it, once."""
    locations.config_file.write_text(
        '[[classify.places]]\nname = "Home{"\nlatitude = 50.0\nlongitude = 4.0\n'
    )
    message = refused(locations).message
    assert "'name' in [[classify.places]] number 1 of config.toml: " in message
    assert message.count("Home{") == 1


def test_a_place_is_named(locations: Locations) -> None:
    """`[[classify.places]]` items are named the same way."""
    locations.config_file.write_text(
        '[[classify.places]]\nname = "Home"\nlatitude = 50.0\nlongitude = 4.0\n'
        '[[classify.places]]\nname = "Sea"\nlatitude = 200.0\nlongitude = 3.0\n'
    )
    assert (
        "'latitude' in [[classify.places]] number 2 ('Sea') of config.toml: "
        in refused(locations).message
    )


@pytest.mark.parametrize(
    "path",
    [
        ("classify", "rules"),
        ("classify", "rules", 5, "match"),
        ("classify", "other", 0),
        ("classify", "rules", 0, "nested", "deeper", 0),
    ],
)
def test_no_item_no_name(path: tuple[str | int, ...]) -> None:
    """Outside an item, past the end of the array or below a plain value: no name."""
    layers: dict[Origin, Layer] = {
        Origin.FILE: {"classify": {"rules": [{"name": "A", "nested": 1}]}}
    }
    assert item_name(layers, path) is None


def test_an_item_name_is_read_from_its_layer() -> None:
    """The name comes from the layer that wrote the array."""
    layers: dict[Origin, Layer] = {
        Origin.FILE: {"classify": {"rules": [{"name": "A"}, {"name": "  "}]}}
    }
    assert item_name(layers, ("classify", "rules", 0, "match")) == "A"
    assert item_name(layers, ("classify", "rules", 1, "match")) is None
