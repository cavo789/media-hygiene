"""Chromium: the shared tile view and naming a face in the large view (2026-11-12).

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python who_walk.py <page.html>`. XL widens the tiles and is kept across a reload;
*Hide the panel* gives the grid the whole width. In the large view, the faces of the
photo are listed (mocked `/person/api/photo`); a click on the face not named opens the
naming line, keys typed there never reach the large view, Enter saves (mocked
`/person/api/names`), the line read back is said, the faces are asked again. Exits 1
with the reason on a failure. Python 3.10 in the image.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

ORIGIN: Final = "http://mh.test/"
SAVED: Final = "Saved in config.toml, read back: Chloé, 1 confirmed face"
FACES: Final = {
    "faces": [
        {
            "key": 7,
            "face": "/person/face/7.jpg",
            "named": {"name": "Paul", "how": "assigned"},
        },
        {"key": 8, "face": "/person/face/8.jpg", "named": None},
    ],
    "people": ["Chloé", "Paul"],
    "writable": True,
}
FILES: Final = (
    "files = Array.from({length: 6}, (_, i) => ({key: 'k' + i, name: 'p' + i,"
    " path: 'C:\\\\Photos\\\\p' + i + '.jpg', preview: '/preview/k' + i + '.jpg',"
    " original: '/o/' + i, chosen: false, tags: {}}));"
)
PIXEL: Final = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000001e221bc330000000049454e44ae426082"
)
# The width of a column of the grid of tiles, as the browser lays it out (no card).
_WIDTH: Final = (
    "parseFloat(getComputedStyle(document.querySelector('main')).gridTemplateColumns)"
)


class _Server:
    """The page, its pictures, the two person routes; what was asked."""

    def __init__(self, html: str) -> None:
        self.html = html
        self.asked: list[tuple[str, object]] = []

    def serve(self, route: Route) -> None:
        """Answer one request of the page."""
        path = route.request.url.removeprefix(ORIGIN[:-1]).split("?")[0]
        body = route.request.post_data or ""
        if path in {"/", ""}:
            route.fulfill(body=self.html, content_type="text/html")
        elif path == "/person/api/photo":
            self.asked.append((path, json.loads(body)))
            route.fulfill(body=json.dumps(FACES), content_type="application/json")
        elif path == "/person/api/names":
            self.asked.append((path, json.loads(body)))
            answer = {"saved": SAVED, "people": ["Chloé", "Paul"]}
            route.fulfill(body=json.dumps(answer), content_type="application/json")
        elif path.endswith((".jpg", ".png")):
            route.fulfill(body=PIXEL, content_type="image/png")
        else:  # the page's own routes: not this walk's
            route.fulfill(status=404, body="")


def _tiles(page: Page) -> list[str]:
    """XL wider than M, kept across a reload; the panel hidden then shown."""
    errors: list[str] = []
    medium = page.evaluate(_WIDTH)
    page.click("#sizes button[data-size='xl']")
    if page.evaluate(_WIDTH) <= medium * 1.5:
        errors.append(f"XL did not widen the tiles ({medium} px)")
    page.click("#sideToggle")
    if not page.evaluate(
        "document.querySelector('.layout').classList.contains('sideHidden')"
    ):
        errors.append("Hide the panel did not hide it")
    page.reload()
    if page.evaluate("document.body.dataset.tileSize") != "xl":
        errors.append("XL is not kept across a reload")
    page.click("#sideToggle")
    page.click("#sizes button[data-size='m']")
    return errors


def _who(page: Page, server: _Server) -> list[str]:
    """Two faces listed; the one not named is named in place, read back."""
    errors: list[str] = []
    page.evaluate(FILES + "current = 0; open();")
    page.wait_for_selector("#viewerWho button.whoFace >> nth=1")
    page.click("#viewerWho button.whoFace >> nth=1")
    field = page.locator("#viewerWhoName input")
    field.type("Chloé f")  # F would go full screen, were the key the view's
    if page.evaluate("Boolean(document.fullscreenElement)"):
        errors.append("a key typed in the name reached the large view")
    field.fill("Chloé")
    field.press("Enter")
    page.wait_for_function(
        f"document.getElementById('viewerSaid').textContent === {json.dumps(SAVED)}"
    )
    named = [body for path, body in server.asked if path == "/person/api/names"]
    if named != [{"action": "move", "name": "Chloé", "faces": [8], "source": ""}]:
        errors.append(f"the naming sent: {named}")
    page.wait_for_timeout(300)
    if sum(path == "/person/api/photo" for path, _ in server.asked) < 2:
        errors.append("the faces were not asked again after the save")
    if not page.evaluate(
        "document.getElementById('viewer').classList.contains('open')"
    ):
        errors.append("the large view closed while naming")
    return errors


def main() -> int:
    """Serve the page and walk the tile view, then the who line.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    server = _Server(Path(sys.argv[1]).read_text("utf-8"))
    failures: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.on("pageerror", lambda error: failures.append(f"page error: {error}"))
        page.route(ORIGIN + "**", server.serve)
        page.goto(ORIGIN)
        failures += _tiles(page)
        failures += _who(page, server)
        browser.close()
    sys.stderr.write(
        "".join(f"{line}\n" for line in failures)
    )  # the log the test shows
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
