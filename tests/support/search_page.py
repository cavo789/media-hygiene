"""The search page opened from the command line, sent calls in order, then stopped."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.services import search_pages as search_service
from tests.integration.tags.test_search_command import _call, fake_server
from tests.support.cli import run

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.review.http import Response
    from media_hygiene.search.app import SearchApp


def serve_search(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, object]]
) -> list[Response]:
    """Open the search page, send the calls in order, stop it; the answers.

    Args:
        cli: The command-line runner.
        monkeypatch: Replaces the page's server with one sending `calls`.
        calls: Each route (`POST /api/…`) and its body.

    Returns:
        The answers, in the order of the calls.
    """
    answers: list[Response] = []

    async def page(app: SearchApp) -> None:
        for route, body in calls:
            answers.append(await _call(app, route, body))

    monkeypatch.setattr(search_service, "serve_until_ended", fake_server(page))
    result = run(cli, "search")
    assert result.exit_code == 0, result.output
    return answers
