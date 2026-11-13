"""Chromium ticks the intruders page and reads its live sentence (0510, 0741).

Run in the Playwright image by `tests/e2e/test_intruders_browser.py`:
`python intruders_walk.py <page.html> <cases.json>`; the page served at a fake origin,
its `api/state` mocked from `cases.json` (`state`), each case (`extensions`, `folders`
ticked) checked against its `sentence` and `button`. Exits 1 with the reasons. The image
runs Python 3.10: nothing newer here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

ORIGIN: Final = "http://intruders.test/"


def _tick(page: Page, table: str, keys: list[str]) -> None:
    """Tick exactly `keys` in one table (the others unticked)."""
    for box in page.query_selector_all(f"#{table} input[type=checkbox]"):
        wanted = box.get_attribute("value") in keys
        if box.is_checked() != wanted:
            box.click()


def main() -> int:
    """Open the page, tick each case, compare the sentence and the button.

    Returns:
        0 when every case reads as expected, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    html = Path(sys.argv[1]).read_text("utf-8")
    given = json.loads(Path(sys.argv[2]).read_text("utf-8"))
    state = json.dumps(given["state"])
    errors: list[str] = []

    def serve(route: Route) -> None:
        if route.request.url.endswith("/api/state"):
            route.fulfill(body=state, content_type="application/json")
        else:
            route.fulfill(body=html, content_type="text/html")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route(ORIGIN + "**", serve)
        page.goto(ORIGIN)
        page.wait_for_selector("#extensions input")
        for case in given["cases"]:
            _tick(page, "extensions", case["extensions"])
            _tick(page, "folders", case["folders"])
            sentence = page.inner_text("#sentence")
            button = page.inner_text("#pick")
            if (sentence, button) != (case["sentence"], case["button"]):
                errors.append(f"{case}: got {sentence!r}, {button!r}")
        browser.close()
    if not errors:
        return 0
    print("\n".join(errors))  # noqa: T201  # the log the test shows
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
