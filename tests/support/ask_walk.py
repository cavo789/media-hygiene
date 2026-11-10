"""Chromium answers the shared ask dialog (0663): Esc and the safe button say no.

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python ask_walk.py <page.html>`; exits 1 with the reason on a failure. The image runs
Python 3.10: nothing newer here.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page

# A hostile line: it must show as text, never as HTML.
LINE: Final = "<b>x</b>"
ASK: Final = (
    "window.__answer = null; window.mhAsk({lines: ['" + LINE + "'], "
    "yes: 'Erase for good', danger: true}).then((a) => { window.__answer = a; });"
)


def _answer(page: Page, act: Callable[[Page], None]) -> tuple[str, bool, str]:
    """Ask once, act, then the focus when it opened, its answer and its lines."""
    page.evaluate(ASK)
    page.wait_for_selector("#mhAsk[open]")
    focused = str(page.evaluate("document.activeElement.id"))
    act(page)
    page.wait_for_function("window.__answer !== null")
    return (
        focused,
        bool(page.evaluate("window.__answer")),
        page.inner_text("#mhAskLines"),
    )


def _dialog_error(errors: list[str], error: str) -> None:
    """Keep a page error when the dialog raised it."""
    if "mhAsk" in error:
        errors.append(error)


def main() -> int:
    """Open the page, ask three times, check each answer.

    Returns:
        0 when every answer is the expected one, 1 otherwise.
    """
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    html = Path(sys.argv[1]).read_text("utf-8")
    errors: list[str] = []
    checks: tuple[tuple[str, Callable[[Page], None], bool], ...] = (
        ("Esc", lambda page: page.keyboard.press("Escape"), False),
        ("safe button", lambda page: page.click("#mhAskNo"), False),
        ("yes button", lambda page: page.click("#mhAskYes"), True),
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        # The page's own calls fail without its server: only the dialog's errors count.
        page.on("pageerror", lambda error: _dialog_error(errors, str(error)))
        page.set_content(html)
        for name, act, expected in checks:
            focused, answer, lines = _answer(page, act)
            if focused != "mhAskNo" or answer is not expected or lines != LINE:
                errors.append(f"{name}: focus {focused}, answer {answer}, {lines!r}")
        browser.close()
    print("\n".join(errors))  # noqa: T201  # the log the test shows
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
