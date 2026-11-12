"""Chromium opens the places map framed on every place of the photos (0339).

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python places_frame_walk.py <page.html> <leaflet.js> <leaflet.css>`. Clusters in
France, Belgium and Italy, and one at exactly 0, 0 (a camera writing an empty GPS as
zeros): on arrival the three countries are on the visible map, the 0, 0 one is not
(the world would show). Exits 1 with the reason on a failure. Python 3.10 in the image.
"""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

ORIGIN: Final = "http://mh.test/"
# Paris, Brussels, Rome; then 0, 0.
# [lat, lon, pictures, videos, place, aside rank (-1: not set aside)].
CLUSTERS: Final = (
    [48.8566, 2.3522, 12, 0, None, -1],
    [50.8503, 4.3517, 5, 1, None, -1],
    [41.9028, 12.4964, 8, 0, None, -1],
    [0.0, 0.0, 3, 0, None, -1],
)
STATE: Final = {"places": [], "clusters": CLUSTERS, "aside": [], "lookup": "off"}
# How long the page may take to frame itself once its clusters are drawn.
FRAMED_MS: Final = 5000
FOLDERS: Final[dict[str, list[object]]] = {
    "folders": [],
    "groups": [],
    "ignored": [],
    "tree": [],
}
# Each cluster's circle: is its centre on the visible map (the drawer's width excluded)?
_SHOWN: Final = """() => {
  const map = document.getElementById("map").getBoundingClientRect();
  const drawer = document.getElementById("drawer");
  const right = drawer.hidden ? map.right : drawer.getBoundingClientRect().left;
  return [...document.querySelectorAll(".leaflet-overlay-pane path")].map((path) => {
    const box = path.getBoundingClientRect();
    const x = box.left + box.width / 2, y = box.top + box.height / 2;
    return x >= map.left && x <= right && y >= map.top && y <= map.bottom;
  });
}"""


class _Site:
    """The page, Leaflet, the two answers it fetches on arrival; no tiles."""

    def __init__(self, files: list[str]) -> None:
        self.page, self.script, self.style = (Path(name).read_bytes() for name in files)

    def serve(self, route: Route) -> None:
        """Answer one request of the page."""
        path = route.request.url.removeprefix(ORIGIN)
        answers = {
            "": (self.page, "text/html"),
            "leaflet.js": (self.script, "text/javascript"),
            "leaflet.css": (self.style, "text/css"),
            "api/state": (json.dumps(STATE).encode(), "application/json"),
            "api/folders": (json.dumps(FOLDERS).encode(), "application/json"),
        }
        if path not in answers:
            route.abort()  # the tiles, anything else: the framing needs none
            return
        body, kind = answers[path]
        route.fulfill(body=body, content_type=kind)


def _check(page: Page, error: type[Exception]) -> list[str]:
    """The three countries on the visible map, 0, 0 off it, within a few seconds."""
    page.wait_for_function(
        "document.querySelectorAll('.leaflet-overlay-pane path').length === 4"
    )
    framed = f"(({_SHOWN})()).every((on, rank) => on === (rank < 3))"
    # Both framings (state, then folders) may take a moment on a loaded runner; a
    # timeout is said below, cluster by cluster.
    with contextlib.suppress(error):
        page.wait_for_function(framed, timeout=FRAMED_MS)
    shown = page.evaluate(_SHOWN)
    errors = [
        f"cluster {CLUSTERS[rank][:2]} is not on the visible map"
        for rank, on in enumerate(shown[:3])
        if not on
    ]
    if len(shown) == len(CLUSTERS) and shown[3]:
        errors.append("the 0, 0 cluster is on screen: the map shows the world")
    return errors


def main() -> int:
    """Serve the page with its clusters, open it at 1366 x 768, check the framing.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import Error, sync_playwright  # noqa: PLC0415

    site = _Site(sys.argv[1:4])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        failures: list[str] = []
        page.on("pageerror", lambda error: failures.append(f"page error: {error}"))
        page.route(ORIGIN + "**", site.serve)
        page.goto(ORIGIN)
        try:
            found = _check(page, Error)
        except Error as error:  # the circles never drawn: say why
            found = [*failures, str(error).splitlines()[0]]
        browser.close()
    sys.stderr.writelines(f"{line}\n" for line in found)  # what the test shows
    return min(len(found), 1)


if __name__ == "__main__":
    sys.exit(main())
