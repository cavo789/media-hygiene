"""Chromium keeps the view in the URL (0666): a reload, Back.

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python view_walk.py <page.html>`; served from a routed origin, so the history
works as on 127.0.0.1. Exits 1 with the reason on a failure. Python 3.10 in the image.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

ORIGIN: Final = "http://mh.test/"
HOSTILE: Final = "?g=<img src=x onerror=window.__hit=1>&tab=</script>"
# The large view opened as the shared viewer opens it: a step pushed, the class set.
OPEN_LARGE: Final = (
    "window.mhView.set({}, { push: true, state: { mhViewer: true } });"
    "document.getElementById('viewer').classList.add('open');"
)
SCROLL_Y: Final = 1200
GROUP: Final = 3
TALL: Final = (
    "document.body.style.minHeight = '5000px'; window.scrollTo(0, 1200);"  # SCROLL_Y
)


def _check(page: Page) -> list[str]:
    """A group kept across a reload; Back closes the large view, the scroll kept."""
    errors: list[str] = []
    page.evaluate(f"window.mhView.set({{ g: {GROUP} }})")
    page.reload()
    if page.evaluate("window.mhView.get({ g: 'int' }).g") != GROUP:
        errors.append("the group is lost on reload")
    page.evaluate(TALL)
    page.evaluate(OPEN_LARGE)
    page.go_back()
    page.wait_for_function(
        "!document.getElementById('viewer').classList.contains('open')"
    )
    if page.evaluate("window.scrollY") != SCROLL_Y:
        errors.append("Back moved the grid")
    if not page.url.startswith(ORIGIN):
        errors.append("Back left the page")
    page.goto(ORIGIN + HOSTILE)
    if (
        page.evaluate("JSON.stringify(window.mhView.get({ g: 'int', tab: 'word' }))")
        != "{}"
    ):
        errors.append("a hostile query string got through")
    if page.evaluate("window.__hit === 1"):
        errors.append("a hostile query string ran")
    return errors


def main() -> int:
    """Serve the page on a routed origin and walk the view.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    html = Path(sys.argv[1]).read_text("utf-8")

    def serve(route: Route) -> None:
        route.fulfill(body=html, content_type="text/html")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.route(ORIGIN + "**", serve)
        page.goto(ORIGIN)
        found = _check(page)
        browser.close()
    if found:
        sys.stderr.write("\n".join(found) + "\n")  # the log the test shows
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
