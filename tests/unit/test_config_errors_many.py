"""Several problems in the settings: a heading, then one bullet each."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.explain_many import BULLET, this_version
from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from tests.unit.test_config_errors import refused

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.paths.locations import Locations

UNKNOWN_TWICE = '[general]\ntimezon = "UTC"\n\n[generl]\nx = 1\n'
MIXED = '[general]\ntimezon = "UTC"\n\n[clean]\npurge_hint_days = "many"\n'


@pytest.fixture(autouse=True)
def _english() -> Iterator[None]:
    """Each test starts in English and leaves the default language behind.

    Yields:
        Control to the test.
    """
    install(Locale.EN)
    yield
    install(Locale.EN)


def test_unknown_names_share_one_heading(locations: Locations) -> None:
    """The explanation is said once; each bullet names a place and its look-alike."""
    locations.config_file.write_text(UNKNOWN_TWICE)
    error = refused(locations)
    heading, *bullets = error.message.split(BULLET)
    assert heading == (
        f"2 settings are unknown to version {this_version()} (a typo, or a setting "
        "of a newer version?):"
    )
    assert bullets == [
        "'timezon' in [general] of config.toml: did you mean 'timezone'?",
        "[generl] in config.toml: did you mean 'general'?",
    ]
    assert error.command == "docker pull cavo789/media-hygiene"


def test_a_refused_value_among_unknown_names(locations: Locations) -> None:
    """Mixed: the heading is general, an unknown name says so in its bullet."""
    locations.config_file.write_text(MIXED)
    heading, *bullets = refused(locations).message.split(BULLET)
    assert heading == "2 settings cannot be used:"
    assert bullets[0] == (
        f"'timezon' in [general] of config.toml: unknown to version {this_version()}; "
        "did you mean 'timezone'?"
    )
    assert bullets[1].startswith("'purge_hint_days' in [clean] of config.toml: ")
    assert not bullets[1].endswith(".")


def test_an_unknown_variable_among_unknown_keys(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A variable and a key: both bullets, the variable named as such."""
    locations.config_file.write_text('[general]\nweather = "sunny"\n')
    monkeypatch.setenv("MEDIA_HYGIENE_GENERAL__TIMEZON", "UTC")
    bullets = refused(locations).message.split(BULLET)[1:]
    assert (
        "The variable MEDIA_HYGIENE_GENERAL__TIMEZON: did you mean "
        "'MEDIA_HYGIENE_GENERAL__TIMEZONE'?"
    ) in bullets
    assert "'weather' in [general] of config.toml" in bullets


def test_french_bullets(locations: Locations) -> None:
    """The heading and the bullets read in French when the file says so."""
    locations.config_file.write_text(f'[general]\nlocale = "fr"\n{MIXED[10:]}')
    install(Locale.FR)
    message = refused(locations).message
    assert message.startswith("2 réglages sont inutilisables :")
    assert "; vouliez-vous dire « timezone » ?" in message
