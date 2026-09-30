"""Screenshots taken inside the Playwright image: `python browser.py <mode> [args]`.

Modes: `review` (the burst review served on 127.0.0.1:8080), `reports <audit> <clean>
<classify>` (report folders of /reports), `terminal <name>...` (SVG terminals in
/shots). Every shot lands in /shots. The image runs Python 3.10: nothing newer here.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page

SCRIPTS: Final = Path(__file__).parent  # the .js files lie next to this one
SHOTS: Final = Path("/shots")
REVIEW: Final = "http://127.0.0.1:8080/"
REPORTS: Final = "file:///reports"
# The bounds of a report section, from its <h2> (found by its emoji) to the next one.
SECTION_JS: Final = (SCRIPTS / "section.js").read_text(encoding="utf-8")
# The bottom of the second burst series: the section stops after it.
SECOND_SERIES_JS: Final = (SCRIPTS / "second_series.js").read_text(encoding="utf-8")
EAGER_JS: Final = (SCRIPTS / "eager_images.js").read_text(encoding="utf-8")
# The bottom of the first group of a classify year page.
FIRST_GROUP_JS: Final = (SCRIPTS / "first_group.js").read_text(encoding="utf-8")
REVIEW_WIDTH: Final = 1600
REPORT_WIDTH: Final = 1180
HEIGHT: Final = 1000
PAUSE_MS: Final = 500
GROUPS_HEIGHT: Final = 620


def load(page: Page, url: str) -> None:
    """Open a page with every lazy image loaded: a full-page shot shows them all.

    Args:
        page: The browser tab.
        url: The page.
    """
    page.goto(url)
    page.evaluate(EAGER_JS)
    page.wait_for_timeout(PAUSE_MS)


def section(page: Page, marker: str, end: str | None = "NEXT") -> dict[str, Any]:
    """Locate a report section.

    Args:
        page: The browser tab, on a report.
        marker: The emoji its title starts with.
        end: `NEXT` (up to the next section), another emoji, or None (to the bottom).

    Returns:
        The clip rectangle of a full-page screenshot.
    """
    clip: dict[str, Any] = page.evaluate(SECTION_JS, [marker, end])
    return clip


def shoot(page: Page, name: str, clip: dict[str, Any] | None = None) -> None:
    """Save a screenshot in /shots.

    Args:
        page: The browser tab.
        name: The file name, without extension.
        clip: The rectangle to keep; the whole page by default.
    """
    page.screenshot(path=SHOTS / f"{name}.png", clip=clip, full_page=True)


def top(page: Page, height: float) -> dict[str, Any]:
    """The clip rectangle of the top of a page, down to `height`."""
    return {"x": 0, "y": 0, "width": page.viewport_size["width"], "height": height}


def review(page: Page) -> None:
    """The birthday series, then a shaken shot set aside; a lake shot set aside too.

    Args:
        page: The browser tab.
    """
    page.goto(REVIEW)
    page.wait_for_selector("#shots figure")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(PAUSE_MS)
    bottom = page.evaluate(
        "document.querySelector('footer').getBoundingClientRect().bottom"
    )
    page.set_viewport_size({"width": REVIEW_WIDTH, "height": int(bottom)})
    page.screenshot(path=SHOTS / "review.png")
    page.keyboard.press("Digit3")
    page.wait_for_selector("#status.saved")
    page.wait_for_timeout(PAUSE_MS)
    page.screenshot(path=SHOTS / "review-aside.png")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(PAUSE_MS)
    page.keyboard.press("Digit4")
    page.wait_for_selector("#status.saved")


def audit_report(page: Page, folder: str) -> None:
    """The index, then the sections of an audit report, and one folder pair page.

    Args:
        page: The browser tab.
        folder: The audit's report folder in /reports.
    """
    load(page, f"{REPORTS}/index.html")
    shoot(page, "index")
    load(page, f"{REPORTS}/{folder}/report.html")
    shoot(page, "report-top", top(page, section(page, "📁", None)["y"]))
    decisions = page.locator("select.decision")
    decisions.nth(2).select_option("swap")
    decisions.nth(1).select_option("skip")
    shoot(page, "report-pairs", section(page, "📁"))
    page.locator("h2:has-text('🧬') ~ .group details").first.locator("summary").click()
    groups = section(page, "🧬")
    shoot(
        page,
        "report-groups",
        {**groups, "height": min(groups["height"], GROUPS_HEIGHT)},
    )
    shoot(page, "report-near", section(page, "🪞"))
    bursts = section(page, "📸")
    shoot(
        page,
        "report-bursts",
        {**bursts, "height": page.evaluate(SECOND_SERIES_JS) - bursts["y"]},
    )
    shoot(page, "report-broken", section(page, "💔", None))
    decisions.first.locator("xpath=ancestor::tr").locator("a").first.click()
    page.wait_for_load_state()
    page.evaluate(EAGER_JS)
    shoot(page, "pair")


def clean_report(page: Page, folder: str) -> None:
    """The top of a clean report, down to its folder pairs.

    Args:
        page: The browser tab.
        folder: The clean's report folder in /reports.
    """
    load(page, f"{REPORTS}/{folder}/report.html")
    pairs = section(page, "📁", "🎲")
    shoot(page, "clean-report", top(page, pairs["y"] + pairs["height"]))


def classify_report(page: Page, folder: str) -> None:
    """The index of a classify report, then the first event of the busiest page."""
    load(page, f"{REPORTS}/{folder}/report.html")
    shoot(page, "classify-report")
    link = page.locator("a[href*='.html#']").first.get_attribute("href") or ""
    load(page, f"{REPORTS}/{folder}/{link.split('#')[0]}")
    shoot(page, "classify-year", top(page, page.evaluate(FIRST_GROUP_JS)))


def terminal(page: Page, name: str) -> None:
    """A terminal drawn as SVG, turned into a picture.

    Args:
        page: The browser tab.
        name: The SVG file name in /shots, without extension.
    """
    page.goto(f"file://{SHOTS}/{name}.svg")
    page.wait_for_timeout(3 * PAUSE_MS)
    page.screenshot(path=SHOTS / f"{name}.png", clip=page.locator("svg").bounding_box())


def main() -> None:
    """Take the screenshots of the mode given on the command line."""
    # Only the Playwright image has it: imported where it runs.
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    mode, arguments = sys.argv[1], sys.argv[2:]
    width = REVIEW_WIDTH if mode == "review" else REPORT_WIDTH
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": HEIGHT}, color_scheme="light"
        )
        if mode == "review":
            review(page)
        elif mode == "reports":
            audit_report(page, arguments[0])
            clean_report(page, arguments[1])
            classify_report(page, arguments[2])
        else:
            for name in arguments:
                terminal(page, name)
        browser.close()


if __name__ == "__main__":
    main()
