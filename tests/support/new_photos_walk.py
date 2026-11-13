"""Chromium follows the people page's analysis of new photos (0588, 0756).

Run in the Playwright image by `tests/e2e/test_people_new_photos_browser.py`:
`python new_photos_walk.py <page.html> <cases.json>`; the page served at a fake
origin, its `/api/people` mocked: each scenario of `cases.json` lists the states its
`GET` answers in turn (the last one repeats; `null` answers 403, off the PC), and a
`POST` of `stop` turns it to `stopped`. The panel's line is checked as the page shows
it. Exits 1 with the reasons. The image runs Python 3.10: nothing newer here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

ORIGIN: Final = "http://people.test/"
SCAN: Final = "api/people"
WAIT_MS: Final = 15_000


class _Scan:
    """The mocked `/api/people` of one scenario."""

    def __init__(self, states: list[dict[str, object] | None]) -> None:
        self.states = states
        self.posts: list[str] = []

    def answer(self, route: Route) -> None:
        """Answer a GET with the next state, a POST by recording its action."""
        if route.request.method == "POST":
            action = json.loads(route.request.post_data or "{}").get("action", "")
            self.posts.append(action)
            if action == "stop":
                self.states = [{"phase": "stopped", "steps": []}]
            route.fulfill(body="{}", content_type="application/json")
            return
        state = self.states[0]
        if len(self.states) > 1:
            self.states = self.states[1:]
        if state is None:
            route.fulfill(status=403, body="{}", content_type="application/json")
        else:
            route.fulfill(body=json.dumps(state), content_type="application/json")


def _line(page: Page, text: str, errors: list[str]) -> None:
    """Wait until the panel's line reads `text`."""
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import (  # noqa: PLC0415
        TimeoutError as PlaywrightTimeout,
    )

    try:
        page.wait_for_function(
            "t => document.getElementById('newPhotosLine').textContent === t",
            arg=text,
            timeout=WAIT_MS,
        )
    except PlaywrightTimeout:
        got = page.inner_text("#newPhotosLine")
        errors.append(f"expected {text!r}, got {got!r}")


def _walk(page: Page, case: dict[str, object], errors: list[str]) -> None:
    """Open the page on one scenario and follow its panel."""
    words: dict[str, str] = case["words"]  # type: ignore[assignment]
    scan = _Scan(case["states"])  # type: ignore[arg-type]
    page.route(ORIGIN + SCAN, scan.answer)
    page.goto(ORIGIN)
    name = case["name"]
    if name == "refused":
        page.wait_for_selector("#newPhotos", state="hidden", timeout=WAIT_MS)
        return
    if page.inner_text("#newPhotosLine") != words["start"]:
        errors.append(f"{name}: the page did not open on the start line")
    _line(page, words["running"], errors)
    if name == "stop":
        page.click("#newPhotosStop")
        _line(page, words["stopped"], errors)
    else:
        _line(page, words["done"], errors)
    if not page.is_visible("#newPhotosShow") or page.is_visible("#newPhotosStop"):
        errors.append(f"{name}: Show visible and Stop hidden expected at the end")
    if scan.posts[:2] != ["prepare", "describe"]:
        errors.append(f"{name}: posted {scan.posts}")
    page.unroute(ORIGIN + SCAN)


def main() -> int:
    """Walk each scenario.

    Returns:
        0 when every scenario reads as expected, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    html = Path(sys.argv[1]).read_text("utf-8")
    cases = json.loads(Path(sys.argv[2]).read_text("utf-8"))
    errors: list[str] = []

    def serve(route: Route) -> None:
        if route.request.url == ORIGIN:
            route.fulfill(body=html, content_type="text/html")
        else:  # the groups and the rest: not this walk's subject
            route.fulfill(status=404, body="{}", content_type="application/json")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case in cases:
            page = browser.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route(ORIGIN + "**", serve)
            _walk(page, case, errors)
            page.close()
        browser.close()
    for error in errors:
        print(error)  # noqa: T201  # the log the test shows
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
