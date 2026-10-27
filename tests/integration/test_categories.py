"""Categories with `--ext`: Czkawka's command, the messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.services.crosscheck import czkawka_command
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations

_WEB: Layer = {"scan": {"categories": {"web": ["png", "gif"]}, "extensions": ["web"]}}


def test_czkawka_gets_the_extensions_of_the_categories(locations: Locations) -> None:
    """`-x` takes extensions only: categories are replaced by theirs."""
    runtime = make_runtime(locations, {"scan": {"extensions": ["video"]}})
    assert "-x 3g2,3gp,avi," in czkawka_command(runtime).render()
    with_web = make_runtime(locations, _WEB)
    assert "-x png,gif " in czkawka_command(with_web).render()


def test_config_lists_every_category(cli: CliRunner, locations: Locations) -> None:
    """Built-in categories and the user's ones, with their extensions and origin."""
    locations.config_file.write_text('[scan.categories]\nphone = ["heic"]\n')
    output = run(cli, "config").output
    assert "Extension categories (--ext)" in output
    assert "built-in" in output
    assert "phone" in output
    assert "heic" in output
