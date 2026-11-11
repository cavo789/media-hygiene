"""Chromium preloads the neighbours of the large view (0675).

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python preload_walk.py <page.html>`. Previews take 300 ms; the second → must show
its photo without waiting, and never more than 2 preview requests in flight.
Exits 1 with the reason on a failure. Python 3.10 in the image.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page, Request, Route

ORIGIN: Final = "http://mh.test/"
DELAY: Final = 0.3
PHOTOS: Final = 6
MAX_IN_FLIGHT: Final = 2
FILES: Final = (
    "files = Array.from({length: 6}, (_, i) => ({key: 'k' + i, name: 'p' + i,"
    " preview: '/preview/k' + i + '.jpg', original: '/o/' + i, chosen: false}));"
    "current = 0; open();"
)
PIXEL: Final = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000001e221bc330000000049454e44ae426082"
)


def _check(page: Page, state: dict[str, int]) -> list[str]:
    """Press → twice; the second photo is already loaded, two requests at most."""
    page.evaluate(FILES)
    page.wait_for_timeout(1500)  # the photo shown and its neighbours arrive
    start = time.monotonic()
    page.evaluate("largeAt(notAside(current, 1))")
    page.evaluate("largeAt(notAside(current, 1))")
    page.wait_for_function("document.getElementById('large').complete")
    errors: list[str] = []
    if time.monotonic() - start > DELAY:
        errors.append("the second → waited for its photo")
    if state["peak"] > MAX_IN_FLIGHT:
        errors.append(f"{state['peak']} preview requests in flight")
    return errors


class _Previews:
    """The mocked previews: 300 ms each, the browser's memory cache after the first."""

    def __init__(self, html: str) -> None:
        self.html = html
        self.state = {"now": 0, "peak": 0}
        self.seen: set[str] = set()

    def started(self, request: Request) -> None:
        """Count a preview request in flight."""
        if "/preview/" in request.url:
            self.state["now"] += 1
            self.state["peak"] = max(self.state["peak"], self.state["now"])

    def ended(self, request: Request) -> None:
        """A preview request is over."""
        if "/preview/" in request.url:
            self.state["now"] -= 1

    def serve(self, route: Route) -> None:
        """Answer the page, or a preview after its delay."""
        path = route.request.url.removeprefix(ORIGIN[:-1])
        if not path.startswith("/preview/"):
            route.fulfill(body=self.html, content_type="text/html")
            return
        if path not in self.seen:
            self.seen.add(path)
            time.sleep(DELAY)
        route.fulfill(body=PIXEL, content_type="image/png")


def main() -> int:
    """Serve the page, mock the previews at 300 ms and walk the arrows.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    mock = _Previews(Path(sys.argv[1]).read_text("utf-8"))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.on("request", mock.started)
        page.on("requestfinished", mock.ended)
        page.on("requestfailed", mock.ended)
        page.route(ORIGIN + "**", mock.serve)
        page.goto(ORIGIN)
        found = _check(page, mock.state)
        browser.close()
    sys.stderr.write("".join(f"{line}\n" for line in found))  # the log the test shows
    return int(bool(found))


if __name__ == "__main__":
    raise SystemExit(main())
