"""`media-hygiene review-sort` from the command line: search's Events view (0439)."""

from __future__ import annotations

import json
import shutil
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.services import search_pages as search_service
from tests.integration.tags.test_search_command import _call, fake_server
from tests.support.cli import run
from tests.support.sorting import EVENT_NAME, build_library

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.search.app import SearchApp


def test_the_verb_opens_the_events_view_and_its_choices_are_saved(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0439: the search's Events view, a one-line notice; a choice there, then sort."""
    shutil.rmtree(locations.data_dir)
    build_library(locations.data_dir)
    assert run(cli, "classify").exit_code == 0
    pages: list[bytes] = []

    async def name_it(app: SearchApp) -> None:
        pages.append((await _call(app, "GET /")).body)
        [card] = json.loads((await _call(app, "GET /api/events")).body)["events"]
        view = json.loads((await _call(app, f"GET /api/events/{card['id']}")).body)
        assert view["hits"][0]["row"]
        body = {"event": card["id"], "name": EVENT_NAME}
        saved = await _call(app, "POST /api/sort/event", body)
        assert saved.status == HTTPStatus.OK, saved.body

    monkeypatch.setattr(search_service, "serve_until_ended", fake_server(name_it))
    result = run(cli, "review-sort")
    assert result.exit_code == 0, result.output
    assert "now opens the 🗂 Events view of 'search'" in result.output
    assert "/events in your browser" in result.output
    assert b'id="eventChoice"' in pages[0]
    sorted_out = run(cli, "sort", "--yes")
    assert (
        "1 choice of the review page applied on top of the workbook"
        in sorted_out.output
    )
