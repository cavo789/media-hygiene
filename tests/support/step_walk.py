"""Chromium follows a step from any page (0661): chip, tab title, end said.

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python step_walk.py <page.html>`; `GET /api/step` is mocked: running at 45 %, then
done. Exits 1 with the reason on a failure. The image runs Python 3.10.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

SITE: Final = "http://mh.test/"
RUNNING: Final = {
    "state": "running",
    "id": "abc",
    "code": None,
    "progress": {"title": "<b>Audit</b>", "done": 45, "total": 100, "current": "x"},
}
DONE: Final = {"state": "done", "id": "abc", "code": 0}


class _Steps:
    """The mocked step: running for the first answers, then done."""

    def __init__(self) -> None:
        """Start running."""
        self.answers = 0

    def answer(self, route: Route) -> None:
        """Answer one poll.

        Args:
            route: The request to `/api/step`.
        """
        self.answers += 1
        said = RUNNING if self.answers < 3 else DONE
        route.fulfill(body=json.dumps(said), content_type="application/json")


def _look(page: Page) -> list[str]:
    """The chip while it runs, then the end said and the title back."""
    problems: list[str] = []
    page.wait_for_selector("#mhStepChip:not([hidden])")
    chip = page.inner_text("#mhStepChip")
    if "45 %" not in chip or "<b>Audit</b>" not in chip:
        problems.append(f"the chip says {chip!r}")
    if not page.title().startswith("45 %"):
        problems.append(f"the tab title is {page.title()!r}")
    page.click("#mhStepChip")
    if not page.is_visible("#mhStepDlg"):
        problems.append("the click opens no dialog")
    page.wait_for_selector("#mhStepChip", state="hidden", timeout=10000)
    if "Audit" not in page.inner_text("#mhSay"):
        problems.append("the end is not said")
    if page.title().startswith("45 %"):
        problems.append("the tab title keeps the progress")
    return problems


def main() -> int:
    """Open the page on a routed origin with the mocked step.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    body = Path(sys.argv[1]).read_text("utf-8")
    steps = _Steps()
    crashes: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda error: crashes.append(str(error)))
        page.route(SITE + "api/step", steps.answer)
        page.route(
            SITE, lambda route: route.fulfill(body=body, content_type="text/html")
        )
        page.goto(SITE)
        problems = _look(page) + crashes
        browser.close()
    for problem in problems:
        print(problem)  # noqa: T201  # the log the test shows
    return int(bool(problems))


if __name__ == "__main__":
    sys.exit(main())
