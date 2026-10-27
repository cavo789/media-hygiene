"""0350: the home server serves the history of the runs under `/history/`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.support.home_serving import serve_home

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner


def test_the_history_is_a_page_of_the_home_server(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Asked through the home server: the page, its bar, the home page still there."""
    answers = serve_home(
        cli, monkeypatch, [("GET /history/", None), ("GET /api/state", None)]
    )
    page, home_state = answers[0], answers[1]
    assert page.status == 200
    body = page.body.decode()
    assert "What each run did" in body
    assert 'id="homeLink"' in body  # the way back home, as every page
    assert home_state.status == 200
