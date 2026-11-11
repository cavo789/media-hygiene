"""Chromium waits with the busy pieces (0664): a slow answer never moves the grid.

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python busy_walk.py <page.html>`; the mocked API answers after 2 s. Exits 1 with the
reason on a failure. The image runs Python 3.10: nothing newer here.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page

ANSWER_MS: Final = 2000
# A button posting, a grid loading, then a hostile error line shown as text.
START: Final = (
    "window.fetch = () => new Promise((ok) =>"
    f" setTimeout(() => ok(new Response('{{}}')), {ANSWER_MS}));"
    "document.body.insertAdjacentHTML('beforeend', '<button id=\"go\">Go</button>"
    '<main id="probe" style="display:grid"></main>\');'
    "window.mhPlaceholders(document.getElementById('probe'), 6);"
    "window.__top = document.getElementById('probe').getBoundingClientRect().top"
    " + window.scrollY;"
    "document.getElementById('go').addEventListener('click', (e) => { window.mhBusy("
    "e.currentTarget, () => fetch('/slow', {method: 'POST'})).then(() => {"
    " window.__done = true; window.mhSay('<b>x</b>', 'error'); }); });"
)


def _check(page: Page) -> list[str]:
    """Click, look while waiting, look after the answer."""
    errors: list[str] = []
    page.evaluate(START)
    page.click("#go")
    if not page.is_disabled("#go"):
        errors.append("the button stays clickable while it waits")
    if page.locator("#probe .mhPlaceholder").count() != 6:
        errors.append("no placeholder tiles")
    page.wait_for_function("window.__done === true")
    if page.is_disabled("#go"):
        errors.append("the button stays disabled after the answer")
    # In the document, not the viewport: the click scrolls the button into view.
    top = page.evaluate(
        "document.getElementById('probe').getBoundingClientRect().top + window.scrollY"
    )
    if top != page.evaluate("window.__top"):
        errors.append(f"the grid moved: {top}")
    if page.inner_text("#mhSay .error p") != "<b>x</b>":
        errors.append("the error line is not shown as text")
    return errors


def main() -> int:
    """Open the page with a slow API and check the waiting.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    html = Path(sys.argv[1]).read_text("utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        errors = _check(page)
        browser.close()
    for error in errors:
        print(error)  # noqa: T201  # the log the test shows
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
