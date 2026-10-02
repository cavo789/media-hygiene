"""`media-hygiene review-sort` from the command line: what it opens, says and saves."""

from __future__ import annotations

import json
import shutil
from typing import TYPE_CHECKING

from media_hygiene.services import sort_reviewing
from tests.support.cli import run
from tests.support.scenes import Shot, write_shot
from tests.support.sort_review import PORT, call, fake_server
from tests.support.sorting import EVENT_NAME, build_library

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.sort_app import SortReviewApp


def test_the_page_is_served_and_the_choices_counted(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ready on its port; one event named; the summary and what comes next."""
    shutil.rmtree(locations.data_dir)
    build_library(locations.data_dir)
    assert run(cli, "classify").exit_code == 0
    pages: list[bytes] = []

    async def name_it(app: SortReviewApp) -> None:
        pages.append(app.page)
        [card] = json.loads((await call(app, "GET /api/state")).body)["events"]
        await call(app, "POST /api/event", {"event": card["id"], "name": EVENT_NAME})

    monkeypatch.setattr(sort_reviewing, "run_server", fake_server(name_it))
    result = run(cli, "review-sort")
    assert result.exit_code == 0, result.output
    assert f"Review ready on port {PORT}" in result.output
    assert "events chosen: 1, photos chosen one by one: 0" in result.output
    assert "sort-decisions.json" in result.output
    assert b"/api/forget" in pages[0]
    assert b"sort-decisions.json" in pages[0]
    sorted_out = run(cli, "sort", "--yes")
    assert (
        "1 choice of the review page applied on top of the workbook"
        in sorted_out.output
    )


def test_nothing_to_review_and_nothing_to_open(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No classify run yet; then a proposal without any event; never a traceback."""
    none = run(cli, "review-sort")
    assert none.exit_code != 0
    assert "Run 'classify' first" in none.output
    shutil.rmtree(locations.data_dir)
    write_shot(
        locations.data_dir / "c/Photos/IMG_1.jpg",
        Shot(1, taken_at="2020:01:01 10:00:00"),
    )
    assert run(cli, "classify").exit_code == 0
    empty = run(cli, "review-sort")
    assert empty.exit_code == 0, empty.output
    assert "nothing to review" in empty.output
    monkeypatch.delenv("MEDIA_HYGIENE_REPORTS_DIR")
    unmounted = run(cli, "review-sort")
    assert unmounted.exit_code != 0
    assert "Traceback" not in unmounted.output
