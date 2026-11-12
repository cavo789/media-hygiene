"""Chromium shows the tile's picture at once in the large view, then the sharp one.

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python sharp_walk.py <page.html>`. Thumbnails answer at once, previews after 1 s.
Opened, a photo shows its loaded tile and its whole path; its preview replaces the tile;
a jump to another photo before the preview arrives never brings the first one back; a
tile without a picture leaves the preview to the browser. Exits 1 with the reason on a
failure. Python 3.10 in the image.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

ORIGIN: Final = "http://mh.test/"
DELAY: Final = 1.0
WAIT_MS: Final = 8000
# Four photos: the first three with a tile picture, the last one without.
SETUP: Final = (
    "files = Array.from({length: 4}, (_, i) => ({key: 'k' + i, name: 'p' + i + '.jpg',"
    " path: 'C:\\\\Photos\\\\June\\\\p' + i + '.jpg', thumb: '/thumb/k' + i + '.png',"
    " preview: '/preview/k' + i + '.jpg', original: '/o/' + i, chosen: false}));"
    "cards = files.map((file, i) => {"
    " const node = document.createElement('article');"
    " if (i < 3) {"
    " const image = new Image(); image.src = file.thumb; node.append(image); }"
    " return node; });"
)
LARGE: Final = "document.getElementById('large')"
SNAPSHOT: Final = (
    f"[{LARGE}.src, {LARGE}.className,"
    " document.getElementById('viewerName').textContent,"
    " Boolean(document.querySelector('#viewerName .viewerFolder'))]"
)
JUMP: Final = (
    "() => { current = 0; open();"
    f" const seen = {SNAPSHOT}; largeAt(2); return seen; }}"
)
PIXEL: Final = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000001e221bc330000000049454e44ae426082"
)


def _opened(page: Page) -> list[str]:
    """The tile at once, the whole path, then a jump: the second photo stays."""
    page.evaluate(SETUP)
    page.wait_for_function("cards.slice(0, 3).every((n) => n.firstChild.complete)")
    src, classes, name, folder = page.evaluate(JUMP)  # opened, then left at once
    errors: list[str] = []
    if not src.endswith("/thumb/k0.png") or "fitted" not in classes:
        errors.append(f"opened, the tile's picture is not shown: {src} ({classes})")
    if name != "C:\\Photos\\June\\p0.jpg" or not folder:
        errors.append(f"the large view names {name!r}, folder dimmed: {folder}")
    page.wait_for_function(f"{LARGE}.src.endsWith('/preview/k2.jpg')", timeout=WAIT_MS)
    page.wait_for_timeout(int(DELAY * 3000))  # every preview asked has arrived
    if not page.evaluate(f"{LARGE}.src").endswith("/preview/k2.jpg"):
        errors.append("the preview of a photo left came back over the one shown")
    return errors


def _without_tile(page: Page) -> list[str]:
    """No tile picture: the preview at once, as before."""
    src = page.evaluate(f"() => {{ largeAt(3); return {LARGE}.src; }}")
    if src.endswith("/preview/k3.jpg"):
        return []
    return [f"without a tile picture, the large view shows {src}"]


def _serve(html: str) -> object:
    """The page, its thumbnails at once and its previews after their delay."""

    def serve(route: Route) -> None:
        path = route.request.url.removeprefix(ORIGIN[:-1])
        if path.startswith("/preview/"):
            time.sleep(DELAY)
        if path.startswith(("/preview/", "/thumb/")):
            route.fulfill(body=PIXEL, content_type="image/png")
            return
        route.fulfill(body=html, content_type="text/html")

    return serve


def main() -> int:
    """Serve the page and walk the large view.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    html = Path(sys.argv[1]).read_text("utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors: list[str] = []
        page.route(ORIGIN + "**", _serve(html))
        page.goto(ORIGIN)
        page.wait_for_timeout(500)  # the page's own API calls, unmocked, fail first
        page.on("pageerror", lambda error: errors.append(f"page error: {error}"))
        errors += _opened(page) + _without_tile(page)
        browser.close()
    sys.stderr.write("".join(f"{line}\n" for line in errors))  # the log the test shows
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
