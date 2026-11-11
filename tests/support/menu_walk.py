"""Chromium counts the controls `/library` shows at load and opens a bar menu (0665).

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python menu_walk.py <page.html>`. Prints the visible count; exits 1 with the reason
when it passes the cap, when ↓ does not open *Move ▾*, Esc does not close it, or the
grid moves.
The image runs Python 3.10.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page

SITE: Final = "http://mh.test/"
# Estimated from the HTML count (33, tests/support/visible_controls.py) plus what
# scripts show at load; the first CI run prints the real figure.
MOST_VISIBLE: Final = 40
COUNT: Final = """() => [...document.querySelectorAll(
  "button, select, textarea, summary, input:not([type=hidden])")]
  .filter((node) => node.checkVisibility({ visibilityProperty: true })).length"""


def _look(page: Page) -> list[str]:
    """The count, then the Move menu by the keyboard."""
    problems: list[str] = []
    shown = page.evaluate(COUNT)
    print(f"visible controls at load: {shown}")  # noqa: T201  # the figure CI shows
    if shown > MOST_VISIBLE:
        problems.append(f"{shown} controls visible at load, more than {MOST_VISIBLE}")
    top = page.evaluate(
        "() => document.getElementById('grid').getBoundingClientRect().top"
    )
    page.focus("#moveMenu > summary")
    page.keyboard.press("ArrowDown")
    if not page.evaluate("() => document.getElementById('moveMenu').open"):
        problems.append("ArrowDown does not open Move")
    page.keyboard.press("Escape")
    if page.evaluate("() => document.getElementById('moveMenu').open"):
        problems.append("Esc does not close Move")
    if page.evaluate("() => document.activeElement.closest('#moveMenu') === null"):
        problems.append("Esc does not bring the focus back to the menu")
    after = page.evaluate(
        "() => document.getElementById('grid').getBoundingClientRect().top"
    )
    if after != top:
        problems.append(f"the grid moved: {top} → {after}")
    return problems


def main() -> int:
    """Open the page on a routed origin.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    body = Path(sys.argv[1]).read_text("utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        page.route(
            SITE, lambda route: route.fulfill(body=body, content_type="text/html")
        )
        page.goto(SITE)
        problems = _look(page)
        browser.close()
    if problems:
        print("\n".join(problems))  # noqa: T201  # the log the test shows
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
