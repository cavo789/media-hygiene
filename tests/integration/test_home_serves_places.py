"""0417: the home server serves the map of `places` itself, under `/places/`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.review.step_watch import served_here
from tests.support.home_serving import serve_home

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_the_map_is_served_under_its_prefix(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page, its state and Leaflet, all through the home server, relative."""
    assert served_here(("places",)) == "/places/"
    locations.config_file.parent.mkdir(parents=True, exist_ok=True)
    locations.config_file.touch()
    answers = serve_home(
        cli,
        monkeypatch,
        [
            ("GET /places/api/state", None),
            ("GET /places", None),
            ("GET /places/", None),
            ("GET /places/api/state", None),
            ("GET /places/leaflet.js", None),
            ("GET /api/state", None),
        ],
    )
    before, redirect, page, state, leaflet, home_state = (*answers,)  # pylint: disable=unbalanced-tuple-unpacking
    assert before.status == 404  # nothing before the page
    assert redirect.status == 303
    assert "Location: /places/" in redirect.headers
    assert page.status == 200, page.body
    assert '"api/state"' in page.body.decode()
    assert 'src="leaflet.js"' in page.body.decode()
    assert state.status == 200
    assert leaflet.status == 200
    assert home_state.status == 200
