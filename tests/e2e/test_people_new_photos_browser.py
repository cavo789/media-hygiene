"""The people page opens at once and follows its new photos, in Chromium (0756).

The panel is driven by the page's own script (`people_new_photos.js.j2`, 0588) against a
mocked `/api/people`: only a browser runs it. Heavy (Playwright image): CI only, where
`MEDIA_HYGIENE_E2E_BROWSER` is set.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import _, install
from media_hygiene.services.people_app_build import PeopleBuild, people_page
from tests.support.pages_browser import (
    BROWSER_ONLY,
    BrowserRun,
    build_browser,
    run_browser,
)

pytestmark = list(BROWSER_ONLY)
_WALK: Final = Path(__file__).parents[1] / "support" / "new_photos_walk.py"
_NEW: Final = 3


def _running(done: int) -> dict[str, object]:
    """The scan's state while it describes the new photos."""
    return {"phase": "running", "steps": [{"done": done, "total": _NEW}]}


_IDLE: Final = {"phase": "idle", "steps": []}
_ASKING: Final = {"phase": "asking", "steps": []}
_SCENARIOS: Final = {
    "done": [
        _IDLE,
        {"phase": "preparing", "steps": []},
        _ASKING,
        _running(1),
        _running(1),
        {"phase": "done", "steps": []},
    ],
    "stop": [_IDLE, _ASKING, _running(1)],
    "refused": [None],
}


def _words() -> dict[str, str]:
    """The lines the panel shows, in the language installed."""
    return {
        "start": _(
            "New photos to analyse: {count}. The groups below stay usable meanwhile…"
        ).format(count=_NEW),
        "running": _("New photos: {done} of {total} analysed; nothing is sent.").format(
            done=1, total=_NEW
        ),
        "done": _("New photos analysed, kept in the cache."),
        "stopped": _(
            "Stopped: the photos left will be analysed the next time this page opens."
        ),
    }


@pytest.mark.parametrize("locale", [Locale.EN, Locale.FR])
def test_the_page_follows_the_new_photos(tmp_path: Path, locale: Locale) -> None:
    """Start line at once, the count, then done or stopped; off the PC: no panel."""
    install(locale)
    try:
        with ThreadPoolExecutor(1) as executor:
            html = people_page(PeopleBuild(executor=executor, names=None, new=_NEW))
        words = _words()
    finally:
        install(Locale.EN)
    page = tmp_path / "people.html"
    page.write_bytes(html)
    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            [
                {"name": name, "states": states, "words": words}
                for name, states in _SCENARIOS.items()
            ]
        ),
        "utf-8",
    )
    (tmp_path / "shots").mkdir()
    build_browser()
    run = BrowserRun(
        name=f"media-hygiene-new-photos-walk-{locale.value}",
        scripts=(_WALK, page, cases),
        args=("/tmp/people.html", "/tmp/cases.json"),  # noqa: S108  # in the container
        network="bridge",  # the script installs playwright first
    )
    assert run_browser(run, tmp_path / "shots") == ""
