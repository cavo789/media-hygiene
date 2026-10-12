"""A config.toml with a typo stops the command with a sentence, never a traceback."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from tests.support.cli import run

if TYPE_CHECKING:
    from collections.abc import Iterator

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


@pytest.fixture(autouse=True)
def _back_to_english() -> Iterator[None]:
    """Leave the default language behind for the next tests.

    Yields:
        Control to the test.
    """
    yield
    install(Locale.EN)


def test_a_typo_is_explained_in_french(cli: CliRunner, locations: Locations) -> None:
    """Brackets survive the console, the pull command is printed whole."""
    locations.config_file.write_text(
        '[general]\nlocale = "fr"\ntimezon = "Europe/Brussels"\n', "utf-8"
    )
    install(Locale.FR)
    result = run(cli, "audit")
    assert result.exit_code == 1
    output = " ".join(result.output.split())
    assert "« timezon » dans [general] de config.toml n'existe pas" in output
    assert "Vouliez-vous dire « timezone » ?" in output
    assert "docker pull cavo789/media-hygiene" in output
    assert "Traceback" not in output
    assert "Extra inputs" not in output
