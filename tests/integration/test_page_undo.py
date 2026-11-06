"""The ↶ Undo of a page's toast runs `mh undo <run>` itself (0601), proven on disk."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene import review
from media_hygiene.review.apply_api import ApplyDesk, ApplyingApp, ApplyOffer
from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request, Response
from media_hygiene.review.write_routes import CHANGES
from media_hygiene.search.undo_api import UNDO_PATH, latest_answer, undo_answer
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from media_hygiene.services.page_undo import PageUndo
from tests.integration.test_clean_undo import clean, manifest
from tests.support.demo import build_demo
from tests.support.page_render import render_page
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_the_page_undoes_its_run_and_reads_the_files_back(
    locations: Locations,
) -> None:
    """The latest run undone: each file found again where it was, the disk as before."""
    build_demo(locations.data_dir)
    before = manifest(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    assert manifest(locations.data_dir) != before
    undo = PageUndo(runtime)
    assert json.loads(latest_answer(undo).body) == {"run_id": run_id}
    body = json.dumps({"run": run_id}).encode()
    answer = asyncio.run(undo_answer(undo, body))
    said = json.loads(answer.body)
    assert answer.status == HTTPStatus.OK
    assert said["meant"] > 0
    assert said["back"] == said["meant"]
    assert said["intact"] is True
    assert manifest(locations.data_dir) == before


def test_only_the_latest_run_is_undone_from_a_page(locations: Locations) -> None:
    """An older or unknown run: 409, the terminal command offered; nothing touched."""
    build_demo(locations.data_dir)
    undo = PageUndo(make_runtime(locations))
    assert json.loads(latest_answer(undo).body) == {"run_id": None}
    answer = asyncio.run(undo_answer(undo, b'{"run": "20990101-000000"}'))
    assert answer.status == HTTPStatus.CONFLICT
    assert "media-hygiene undo 20990101-000000" in json.loads(answer.body)["error"]
    assert asyncio.run(undo_answer(undo, b"{}")).status == HTTPStatus.BAD_REQUEST


def test_the_undo_route_is_a_pc_only_change() -> None:
    """Never reachable from the phone: it moves files."""
    assert UNDO_PATH in CHANGES


class _Page:
    """A page's app: answers anything else."""

    async def handle(self, request: Request) -> Response:
        """Answer a teapot.

        Args:
            request: The request.

        Returns:
            The response.
        """
        return Response(HTTPStatus.IM_A_TEAPOT, request.path.encode())


def _applying(offer_undo: PageUndo | None) -> ApplyingApp:
    """A review's app as the home server wraps it."""
    offer = ApplyOffer(None, lambda: False, offer_undo)
    return ApplyingApp(_Page(), ApplyDesk(offer, Ending()))


def _asked(app: ApplyingApp, method: str, body: bytes = b"") -> Response:
    """Ask the route as the page does."""
    headers = {"host": "localhost", "content-type": "application/json"}
    return asyncio.run(app.handle(Request(method, UNDO_PATH, headers, body)))


def test_a_review_page_undoes_its_run_and_the_disk_is_as_before(
    locations: Locations,
) -> None:
    """0621: the route beside the review's app; the files found back on disk."""
    build_demo(locations.data_dir)
    before = manifest(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    app = _applying(PageUndo(runtime))
    assert json.loads(_asked(app, "GET").body) == {"run_id": run_id}
    answer = _asked(app, "POST", json.dumps({"run": run_id}).encode())
    said = json.loads(answer.body)
    assert answer.status == HTTPStatus.OK
    assert said["back"] == said["meant"] > 0
    assert manifest(locations.data_dir) == before


def test_the_route_stays_on_the_pc_and_on_the_pages_given_it(
    locations: Locations,
) -> None:
    """Another host refused; a page served apart (no Undo): its app answers."""
    app = _applying(PageUndo(make_runtime(locations)))
    far = Request("GET", UNDO_PATH, {"host": "example.com"}, b"")
    assert asyncio.run(app.handle(far)).status == HTTPStatus.FORBIDDEN
    assert _asked(_applying(None), "GET").status == HTTPStatus.IM_A_TEAPOT


@pytest.mark.parametrize(
    "template",
    [
        "review.html.j2",
        "near_review.html.j2",
        "pairs_review.html.j2",
        "unwanted_review.html.j2",
        "intruders_review.html.j2",
    ],
)
def test_every_review_with_apply_now_shows_the_toast(
    template: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exactly one toast, its Undo path relative to the page."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")
    page = render_page(template)
    assert page.count('id="mhUndoToast"') == 1
    assert 'id="applyNow"' in page


def test_the_undo_said_stays_after_the_page_reloads() -> None:
    """What the disk holds is kept for the reload, like the step's end."""
    source = Path(review.__file__).with_name("templates") / "apply_now.html.j2"
    text = source.read_text("utf-8")
    assert "window.sessionStorage.setItem(ENDED_KEY, undone)" in text
