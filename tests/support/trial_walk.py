"""Chromium clicks *Try on one month* on library's Events tab (0640, 0800).

Run in the Playwright image by `tests/e2e/test_sort_trial_browser.py`:
`python trial_walk.py <answers.json>`; the page and the answers the real app gave
(`page`; `answers`: "METHOD path" → status and body) served at a fake origin. The walk
opens the Events tab, clicks the button, confirms, then reads the grid back: every new
folder the run reported (`folders`) is on the tiles; a path the app was not asked
first is an error. Exits 1 with the reasons. The image runs Python 3.10: nothing
newer here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

ORIGIN: Final = "http://library.test"
_RUN: Final = "/api/sort/trial/run"

_WAIT_MS: Final = 15000


def _read_back(page: Page, folders: list[str], posted: list[str]) -> list[str]:
    """What the page shows after the trial, against what the app moved.

    Returns:
        The differences, empty when it matches.
    """
    grid = page.inner_text("#grid")
    errors = [
        f"{one!r} not on the tiles: {grid[:400]!r}"
        for one in folders
        if one not in grid
    ]
    if posted != [_RUN]:
        errors.append(f"the trial was posted {len(posted)} times")
    if not page.is_visible("#trialRest"):
        errors.append("no 'Sort the rest' button after the trial")
    return errors


def main() -> int:
    """Open the page, try the month, read the grid back.

    Returns:
        0 when the grid shows the month at its new place, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    given = json.loads(Path(sys.argv[1]).read_text("utf-8"))
    errors: list[str] = []
    posted: list[str] = []

    def serve(route: Route) -> None:
        path = route.request.url[len(ORIGIN) :].split("?")[0]
        if not path.startswith("/api/"):
            route.fulfill(body=given["page"], content_type="text/html")
            return
        if path == _RUN:
            posted.append(path)
        key = f"{route.request.method} {path}"
        if key not in given["answers"]:
            errors.append(f"not answered: {key} {route.request.post_data}")
        status, body = given["answers"].get(key, (404, "{}"))
        route.fulfill(status=status, body=body, content_type="application/json")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda error: errors.append(f"page error: {error}"))
        page.route(ORIGIN + "/**", serve)
        page.goto(ORIGIN + "/library")
        page.click("#tabEvents")
        page.wait_for_selector("#trialTry:visible", timeout=_WAIT_MS)
        page.click("#trialTry")
        page.click("#trialYes")
        page.wait_for_selector("#trialUndo:visible", timeout=_WAIT_MS)
        page.wait_for_selector("#grid > *", timeout=_WAIT_MS)
        errors.extend(_read_back(page, given["folders"], posted))
        page.screenshot(path="/shots/trial.png", full_page=True)
        browser.close()
    sys.stdout.write("".join(f"{error}\n" for error in errors))  # the test's log
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
