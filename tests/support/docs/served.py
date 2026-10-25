"""The pages served on 127.0.0.1:8088, shot inside the Playwright image by `browser.py`.

The reviews (bursts, near, pairs, junk), the home and browse pages, search, people
and places.
Copied next to `browser.py`, which imports it; Python 3.10 there: nothing newer here.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page

SCRIPTS: Final = Path(__file__).parent  # the .js files lie next to this one
SHOTS: Final = Path("/shots")
SERVED: Final = "http://127.0.0.1:8088/"
SHOTS_SHOWN_JS: Final = (SCRIPTS / "shots_shown.js").read_text(encoding="utf-8")
EAGER_JS: Final = (SCRIPTS / "eager_images.js").read_text(encoding="utf-8")
# A frame of each video drawn, not a black box: seek a little, wait for the picture.
VIDEO_SEEK_JS: Final = (
    "() => document.querySelectorAll('#shots video')"
    ".forEach((video) => { video.currentTime = 3; })"
)
VIDEO_SHOWN_JS: Final = (
    "() => [...document.querySelectorAll('#shots video')]"
    ".every((video) => video.readyState >= 2 && !video.seeking)"
)
HITS_SHOWN_JS: Final = (
    "() => document.querySelectorAll('#grid article').length > 0 && "
    "[...document.querySelectorAll('#grid img')].every((image) => image.complete)"
)
FACES_SHOWN_JS: Final = (
    "() => [...document.querySelectorAll('#groups img')]"
    ".every((image) => image.complete)"
)
# Every tile of the map drawn: a grey map fails the run, it never reaches the docs.
TILES_SHOWN_JS: Final = (
    "() => { const tiles = [...document.querySelectorAll('.leaflet-tile')]; "
    "return tiles.length > 0 && "
    "tiles.every((tile) => tile.classList.contains('leaflet-tile-loaded')); }"
)
PREVIEWS_SHOWN_JS: Final = (
    "() => [...document.querySelectorAll('.thumbs img')]"
    ".every((image) => image.complete)"
)
AUDIT_MS: Final = 300_000
TILES_MS: Final = 30_000
PAUSE_MS: Final = 500
VIDEO_PAUSE_MS: Final = 2000  # the loading spinner fades out


def shots_shown(page: Page) -> None:
    """Wait until the pictures of the review's group show, then for transitions."""
    page.wait_for_function(SHOTS_SHOWN_JS)
    page.wait_for_timeout(PAUSE_MS)


def _fit(page: Page) -> None:
    """Make the window as tall as the page: one shot shows all of it."""
    height = page.evaluate("document.documentElement.scrollHeight")
    page.set_viewport_size({"width": page.viewport_size["width"], "height": height})


def review(page: Page) -> None:
    """The birthday series with its proposal, then the shaken shot set aside."""
    page.goto(SERVED)
    page.wait_for_selector("#shots figure")
    page.keyboard.press("ArrowRight")
    shots_shown(page)
    _fit(page)
    shots_shown(page)
    page.screenshot(path=SHOTS / "review.png")
    for done in ("#status.saved", "#shots figure.aside"):  # proposed: taken back, aside
        page.keyboard.press("Digit5")
        page.wait_for_selector(done)
    shots_shown(page)
    page.screenshot(path=SHOTS / "review-aside.png")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(PAUSE_MS)
    page.keyboard.press("Digit4")
    page.wait_for_selector("#status.saved")


def near(page: Page) -> None:
    """The first group to check, then the re-encoded video; nothing decided."""
    page.goto(SERVED)
    page.wait_for_selector("#shots figure")
    page.wait_for_selector("#status:not(:empty)")  # decisions.json read back
    shots_shown(page)
    _fit(page)
    shots_shown(page)
    page.screenshot(path=SHOTS / "review-near.png")
    # The video frees the most: first by space freed, the order the page remembers.
    page.evaluate("localStorage.setItem('near-order', 'gain')")
    page.reload()
    page.wait_for_selector("#shots video")
    page.evaluate(VIDEO_SEEK_JS)
    page.wait_for_function(VIDEO_SHOWN_JS)
    _fit(page)
    page.wait_for_timeout(VIDEO_PAUSE_MS)
    page.screenshot(path=SHOTS / "review-near-video.png")


def pairs(page: Page) -> None:
    """The folder pairs review: the largest pair shown, nothing decided."""
    page.goto(SERVED)
    page.wait_for_selector("#keptIn div")
    page.wait_for_selector("#status:not(:empty)")  # decisions.json read back
    shots_shown(page)
    _fit(page)
    shots_shown(page)
    page.screenshot(path=SHOTS / "review-pairs.png")


def junk(page: Page) -> None:
    """The photos most likely unwanted: the first group, everything still proposed."""
    page.goto(SERVED)
    page.wait_for_selector("#shots figure")
    page.wait_for_function(FACES_SHOWN_JS.replace("#groups", "#shots"))
    _fit(page)
    page.wait_for_timeout(PAUSE_MS)
    page.screenshot(path=SHOTS / "review-junk.png")


def home(page: Page) -> None:
    """The home page after its own audit: the steps with their times, the next step."""
    page.goto(SERVED)
    page.wait_for_selector("#auditStart")
    page.click("#auditStart")
    page.wait_for_selector("#auditEnd a", timeout=AUDIT_MS)  # link to the new report
    page.wait_for_selector(".thumbs img", timeout=AUDIT_MS)
    page.evaluate(EAGER_JS)  # lazy thumbnails: a full-page shot shows them all
    page.wait_for_function(PREVIEWS_SHOWN_JS)
    # The fixed sidebar and top bar drawn once, at the top: no scroll, no skip link.
    page.evaluate("() => { document.activeElement.blur(); window.scrollTo(0, 0); }")
    _fit(page)
    page.mouse.move(5, 5)
    page.wait_for_timeout(PAUSE_MS)
    page.screenshot(path=SHOTS / "home.png")


def browse(page: Page, name: str) -> None:
    """The folder view: a folder opened, two photos picked and set aside, saved.

    Args:
        page: The browser tab.
        name: The last part of the folder to open (its path ends with it).
    """
    page.goto(SERVED)
    page.wait_for_selector("#tree .folder")
    page.evaluate(
        "document.querySelectorAll('#tree ul[hidden]')"
        ".forEach((list) => { list.hidden = false; })"
    )
    page.locator(f'.folder[data-path$="{name}"]').first.click()
    page.wait_for_selector("#grid article")
    page.wait_for_function(HITS_SHOWN_JS)
    page.locator("#grid article").nth(1).click()
    page.locator("#grid article").nth(2).click(modifiers=["Control"])
    page.click("#setAside")
    page.wait_for_selector("#grid .badge")
    page.wait_for_selector("#applyNow:not([hidden])")
    page.mouse.move(5, 5)
    page.wait_for_timeout(PAUSE_MS)
    page.screenshot(path=SHOTS / "browse.png")
    # Put them back: `clean --decisions` would set the two photos aside in the story.
    page.locator("#grid article").nth(1).click()
    page.locator("#grid article").nth(2).click(modifiers=["Control"])
    page.click("#takeBack")
    page.wait_for_function(
        "() => document.querySelectorAll('#grid .badge').length === 0"
    )


def search(page: Page, words: str) -> None:
    """The search page: the words typed, the grid of the photos found.

    Args:
        page: The browser tab.
        words: What to type in the search field.
    """
    page.goto(SERVED)
    page.wait_for_selector("#text")
    page.fill("#text", words)
    page.press("#text", "Enter")
    page.wait_for_function(HITS_SHOWN_JS)
    page.wait_for_timeout(PAUSE_MS)
    page.screenshot(path=SHOTS / "search.png")


def people(page: Page, name: str) -> None:
    """The people page: the largest group named, the name read back from config.toml.

    Args:
        page: The browser tab.
        name: The name typed on the first group.
    """
    page.goto(SERVED)
    page.wait_for_selector("#groups section input")
    page.fill("#groups section input", name)
    page.press("#groups section input", "Enter")
    page.wait_for_selector("#status.saved")
    page.wait_for_function(FACES_SHOWN_JS)
    page.wait_for_timeout(PAUSE_MS)
    page.screenshot(path=SHOTS / "people.png", full_page=True)


def places(page: Page, name: str) -> None:
    """The places map: the largest cluster named and saved, the OSM tiles drawn.

    Args:
        page: The browser tab.
        name: The name typed on the park's cluster.
    """
    page.goto(SERVED)
    page.wait_for_selector("#clusters li button.link")
    page.locator("#clusters li button.link").first.click()  # "Name this place"
    page.fill("#name", name)
    page.press("#name", "Enter")
    page.wait_for_selector("#status.saved")
    page.mouse.move(5, 5)  # off the map: no hover tooltip on a circle
    page.wait_for_function(TILES_SHOWN_JS, timeout=TILES_MS)  # raises if tiles fail
    page.wait_for_timeout(PAUSE_MS)
    page.screenshot(path=SHOTS / "places.png")
