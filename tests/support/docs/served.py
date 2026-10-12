"""The pages served on 127.0.0.1:8088, shot inside the Playwright image by `browser.py`.

The burst review, the near-duplicate review, the search page and the people page.
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
    "() => document.querySelectorAll('#grid .hit').length > 0 && "
    "[...document.querySelectorAll('#grid img')].every((image) => image.complete)"
)
FACES_SHOWN_JS: Final = (
    "() => [...document.querySelectorAll('#groups img')]"
    ".every((image) => image.complete)"
)
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
