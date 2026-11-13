"""*Try on one month* in Chromium, against what the real app answered (0800).

The test sorts the latest month for real through the library app (files moved on disk,
read back), then hands Chromium the page and those answers: the walk clicks the button,
confirms, and reads the grid back, each tile at its new folder. Heavy (Playwright
image): CI only, where `MEDIA_HYGIENE_E2E_BROWSER` is set.
"""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request
from media_hygiene.search.events_desk import EVENTS_PATH
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.trial_api import TRIAL_PATH, TRIAL_RUN_PATH
from media_hygiene.services.search_app import SearchBuild, search_app
from tests.integration.test_sort_event import two_events
from tests.support.pages_browser import (
    BROWSER_ONLY,
    BrowserRun,
    build_browser,
    run_browser,
)

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.search.app import SearchApp
    from media_hygiene.services.runtime import Runtime

pytestmark = list(BROWSER_ONLY)
_WALK: Final = Path(__file__).parents[1] / "support" / "trial_walk.py"
_HOST: Final = {"host": "127.0.0.1", "content-type": "application/json"}
_SEARCH: Final = {
    "text": "", "day_from": None, "day_to": None, "folder": "", "source": None,
    "sorting": "all", "order": "best", "missing": "all", "place": "", "kind": "all",
    "aside": False, "within": "", "more": 0, "album": None,
}  # fmt: skip  # what the page posts when it opens
# What the page asks when it opens and when the Events tab shows, before the trial.
_OPENING: Final = (
    ("GET", "/api/albums", None),
    ("GET", "/api/chosen", None),
    ("GET", "/api/events/", None),
    ("GET", "/api/found-events", None),
    ("GET", "/api/late-events", None),
    ("GET", "/api/step", None),
    ("POST", "/api/alive", {"leaving": False}),
    ("POST", "/api/place", {"action": "list"}),
    ("POST", "/api/search", _SEARCH),
    ("GET", EVENTS_PATH, None),
    ("GET", TRIAL_PATH, None),
)


def _ask(app: SearchApp, method: str, sent: tuple[str, object]) -> tuple[int, str]:
    """One request to the real app.

    Returns:
        Its status and body.
    """
    path, body = sent
    data = b"" if body is None else json.dumps(body).encode()
    answer = asyncio.run(app.handle(Request(method, path, _HOST, data)))
    return int(answer.status), answer.body.decode("utf-8")


def _tried(locations: Locations) -> tuple[Runtime, str, dict[str, tuple[int, str]]]:
    """The library app asked what the page asks, then the trial run, for real.

    Returns:
        The runtime, the page, and each answer by "METHOD path".
    """
    runtime, _workbook, _sizes = two_events(locations)
    with (
        SearchIndex.open(locations.index_file) as search,
        ThreadPoolExecutor(1) as executor,
    ):
        app = search_app(
            runtime, search, SearchBuild("/library", None, Ending(), executor)
        )
        status, page = _ask(app, "GET", ("/library", None))
        assert status == HTTPStatus.OK
        answers = {
            f"{method} {path}": _ask(app, method, (path, body))
            for method, path, body in _OPENING
        }
        answers[f"POST {TRIAL_RUN_PATH}"] = _ask(app, "POST", (TRIAL_RUN_PATH, {}))
    return runtime, page, answers


def test_the_month_is_tried_then_shown_at_its_new_place(
    tmp_path: Path, locations: Locations
) -> None:
    """The button, the question, the run: the tiles say where the files went."""
    runtime, page, answers = _tried(locations)
    offer = json.loads(answers[f"GET {TRIAL_PATH}"][1])["offer"]
    assert offer is not None
    status, body = answers[f"POST {TRIAL_RUN_PATH}"]
    assert status == HTTPStatus.OK
    run = json.loads(body)
    assert run["intact"]
    assert run["moved"] == offer["files"]
    folders = sorted({hit["folder"] for hit in run["hits"]})
    assert folders
    for hit in run["hits"]:  # read back: each file is at the place the page shows
        assert runtime.mapper.to_container(hit["path"]).is_file(), hit["path"]
    given = tmp_path / "answers.json"
    given.write_text(
        json.dumps({"page": page, "answers": answers, "folders": folders}), "utf-8"
    )
    (tmp_path / "shots").mkdir()
    build_browser()
    walk = BrowserRun(
        name="media-hygiene-trial-walk",
        scripts=(_WALK, given),
        args=("/tmp/answers.json",),  # noqa: S108  # in the container
        network="bridge",  # the script installs playwright first
    )
    assert run_browser(walk, tmp_path / "shots") == ""
