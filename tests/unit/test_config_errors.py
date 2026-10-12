"""A refused configuration is explained in the user's language, key by key."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.known_keys import fields_at
from media_hygiene.config.loader import load_settings
from media_hygiene.constants import Locale
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import install

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations

# Pydantic's own English, never shown to a French user.
_PYDANTIC_WORDS = ("Extra inputs", "Input should", "not permitted", "valid boolean")


@pytest.fixture(autouse=True)
def _english() -> Iterator[None]:
    """Each test starts in English and leaves the default language behind.

    Yields:
        Control to the test.
    """
    install(Locale.EN)
    yield
    install(Locale.EN)


def refused(locations: Locations, cli: Layer | None = None) -> ConfigError:
    """Load the settings, expecting a refusal.

    Args:
        locations: Mount points of the test.
        cli: Command-line overrides.

    Returns:
        The error raised.
    """
    with pytest.raises(ConfigError) as caught:
        load_settings(locations, cli)
    return caught.value


def test_an_unknown_key_says_where_and_how_to_update(locations: Locations) -> None:
    """A key of a newer version: named, with its table, the file and the pull."""
    locations.config_file.write_text('[general]\nweather = "sunny"\n')
    error = refused(locations)
    assert "'weather' in [general] of config.toml is unknown to" in error.message
    assert "Did you mean" not in error.message
    assert error.command == "docker pull cavo789/media-hygiene"


def test_a_near_miss_suggests_the_known_key(locations: Locations) -> None:
    """`timezon` is a typo of `timezone`: the message says so."""
    locations.config_file.write_text('[general]\ntimezon = "Europe/Brussels"\n')
    assert "Did you mean 'timezone'?" in refused(locations).message


def test_an_unknown_table_suggests_the_known_one(locations: Locations) -> None:
    """A whole `[generl]` table is named, with its look-alike."""
    locations.config_file.write_text('[generl]\nlocale = "fr"\n')
    message = refused(locations).message
    assert "[generl] in config.toml is unknown" in message
    assert "Did you mean 'general'?" in message


def test_a_bad_type_in_french_has_no_pydantic_english(locations: Locations) -> None:
    """Every common error reads in French, an unknown key included."""
    locations.config_file.write_text(
        '[general]\nverbosity = "loud"\ntimezon = "UTC"\n[clean]\nconfirm = "maybe"\n'
        "[classify.ai]\nconcurrency = 0\n"
    )
    install(Locale.FR)
    error = refused(locations)
    assert "« confirm » dans [clean] de config.toml : true ou false" in error.message
    assert "au moins 1 est attendu, pas 0" in error.message
    assert "vouliez-vous dire « timezone » ?" in error.message
    assert not any(word in error.message for word in _PYDANTIC_WORDS)


def test_a_value_error_keeps_its_translated_reason(locations: Locations) -> None:
    """A validator of the project already speaks to the user: its words are kept."""
    locations.config_file.write_text('[general]\ntimezone = "Mars/Olympus"\n')
    error = refused(locations)
    assert error.message.startswith("'timezone' in [general] of config.toml: ")
    assert "Value error" not in error.message
    assert error.command is None


def test_another_error_type_keeps_pydantic_words(locations: Locations) -> None:
    """A rare type without a sentence of its own still names the key."""
    locations.config_file.write_text("[scan]\nextensions = 3\n")
    assert "'extensions' in [scan] of config.toml: " in refused(locations).message


def test_a_list_item_names_its_list(locations: Locations) -> None:
    """A wrong item of a plain list names the list; a boolean reads as in TOML."""
    locations.config_file.write_text(
        '[scan]\nextensions = [".jpg", 3]\n[general]\nverbosity = true\n'
    )
    message = refused(locations).message
    assert "'extensions' in [scan] of config.toml: a text between quotes" in message
    assert "is expected, not true\n" in message


def test_a_rule_is_named_by_its_number(locations: Locations) -> None:
    """`[[classify.rules]]` items are counted from 1, as a reader counts them."""
    locations.config_file.write_text(
        '[[classify.rules]]\nname = "Birthday"\nmatch = "calendar"\n'
        'dates = "02-30"\n[[classify.rules]]\nname = "Other"\n'
    )
    message = refused(locations).message
    assert "• [[classify.rules]] number 1 in config.toml: rule" in message
    assert (
        "'match' in [[classify.rules]] number 2 ('Other') of config.toml: this "
        "setting is required" in message
    )


def test_a_path_leading_nowhere_has_no_keys() -> None:
    """Below a plain value there is no table, hence nothing to suggest."""
    assert not fields_at(("general", "locale", "deeper"))
    assert "timezone" in fields_at(("general",))


def test_an_unknown_variable_is_named_as_a_variable(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A variable with a typo is refused, with the known one it looks like."""
    monkeypatch.setenv("MEDIA_HYGIENE_GENERAL__TIMEZON", "UTC")
    monkeypatch.setenv("MEDIA_HYGIENE_REPORTS_DIR", str(locations.config_file.parent))
    error = refused(locations)
    assert error.message.startswith(
        "The variable MEDIA_HYGIENE_GENERAL__TIMEZON is unknown to version"
    )
    assert "Did you mean 'MEDIA_HYGIENE_GENERAL__TIMEZONE'?" in error.message
    assert error.command is not None


def test_a_bad_variable_value_names_the_variable(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A refused value from the environment points at the variable, not the file."""
    monkeypatch.setenv("MEDIA_HYGIENE_GENERAL__VERBOSITY", "loud")
    monkeypatch.setenv("MEDIA_HYGIENE_CLASSIFY__AI", '{"modle": "llava"}')
    message = refused(locations).message
    assert "The variable MEDIA_HYGIENE_GENERAL__VERBOSITY: one of 'error'" in message
    assert "'modle' in the variable MEDIA_HYGIENE_CLASSIFY__AI: unknown" in message


def test_a_bad_option_value_names_the_command_line(locations: Locations) -> None:
    """A refused value typed as an option is said to come from the command line."""
    error = refused(locations, {"general": {"color": "pink"}})
    assert error.message.startswith("'color' on the command line: one of")


def test_a_validator_reason_reads_in_french(locations: Locations) -> None:
    """The project's own reasons are translated too: no English left in the sentence."""
    locations.config_file.write_text(
        '[[classify.rules]]\nname = "Anniversaire"\nmatch = "calendar"\n'
        'dates = "02-30"\ncategory = "Fêtes"\n'
    )
    install(Locale.FR)
    message = refused(locations).message
    assert message == (
        "[[classify.rules]] n° 1 dans config.toml : règle « Anniversaire » : "
        "« 02-30 » n'est pas un jour qui existe."
    )
    assert not any(word in message for word in ("rule ", "is not", "day", "exists"))
