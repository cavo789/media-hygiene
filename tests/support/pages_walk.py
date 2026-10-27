"""The pages of `mh` walked in Chromium: `python pages_walk.py <port>`.

Run by `tests/e2e/test_pages_browser.py` against the home page `mh` alone serves on
127.0.0.1:<port> (the container joins the host's network). Each step is timed by the
browser or this script; the figures, and the clock of the search steps (for Docker's
events), land in /shots/walk.json. The image runs Python 3.10: nothing newer here.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page

OUTPUT: Final = Path("/shots/walk.json")
SEARCH_API: Final = "/api/search"
HOME_READY: Final = "#runDlg"  # the home page's own dialog: no other page has it
PAGE_READY: Final = "#homeLink"  # *Back to the home page*, on every page mh opened
SHOWN_MS: Final = 30_000  # a page served by the home server (search, browse)
STEP_MS: Final = 120_000  # a console step, or a page of its own server
ROUNDS: Final = (
    10  # returns from a page of its own server, in a row (0354: 1 in 3 failed)
)
REVIEWS: Final = ("review", "review-pairs", "review-junk")
MARK_JS: Final = "() => { window.mhWalk = 1; }"
MARKED_JS: Final = "() => window.mhWalk === 1"
AVAILABLE_JS: Final = (
    "(name) => Boolean(BY_ID[name]) && statusOf(BY_ID[name]).available"
)
RUN_JS: Final = "(name) => onRun(name)"
STEP_JS: Final = "() => fetch('/api/step', { cache: 'no-store' }).then((r) => r.json())"
# The search page timed by the browser: its navigation, its first answer of /api/search.
TIMING_JS: Final = """() => {
  const nav = performance.getEntriesByType("navigation")[0];
  const asked = performance.getEntriesByType("resource")
    .filter((entry) => entry.name.includes("/api/search"))[0];
  return { loaded_ms: nav ? nav.domContentLoadedEventEnd : null,
           first_search_ms: asked ? asked.responseEnd : null };
}"""


def _searched(answer: Any) -> bool:  # noqa: ANN401  # Playwright's Response
    """Tell whether an answer is the search page's.

    Args:
        answer: An answer the tab received.

    Returns:
        True for `/api/search`.
    """
    return SEARCH_API in str(answer.url)


def open_from_home(page: Page, name: str) -> dict[str, Any]:
    """Click a page the home server serves itself, then come back to the home page.

    Args:
        page: The tab, on the home page.
        name: The step (`search`, `browse`).

    Returns:
        The timings, in ms.
    """
    start = time.monotonic()
    if name == "search":
        with page.expect_response(_searched, timeout=SHOWN_MS):
            page.evaluate(RUN_JS, name)
    else:
        page.evaluate(RUN_JS, name)
    page.wait_for_selector(PAGE_READY, timeout=SHOWN_MS)
    shown = (time.monotonic() - start) * 1000
    measured: dict[str, Any] = page.evaluate(TIMING_JS)
    start = time.monotonic()
    page.click(PAGE_READY)
    page.wait_for_selector(HOME_READY, state="attached", timeout=SHOWN_MS)
    back = (time.monotonic() - start) * 1000
    return {**measured, "click_to_shown_ms": round(shown), "back_home_ms": round(back)}


def console_step(page: Page) -> dict[str, Any]:
    """`history` from the home page: it runs in the window of mh, the page stays.

    Args:
        page: The tab, on the home page.

    Returns:
        What the dialog said, the step's end, the time it took.
    """
    page.evaluate(MARK_JS)
    start = time.monotonic()
    page.evaluate(RUN_JS, "history")
    said = page.locator("#runDlg [role=status]").inner_text(timeout=SHOWN_MS)
    page.wait_for_selector("#runDlg", state="hidden", timeout=STEP_MS)
    took = (time.monotonic() - start) * 1000
    step: dict[str, Any] = page.evaluate(STEP_JS)
    return {
        "said": said,
        "step": step,
        "stayed": page.evaluate(MARKED_JS),  # never reloaded nor closed
        "took_ms": round(took),
    }


def own_server_rounds(page: Page) -> dict[str, Any]:
    """A review (its own server) then back, ten times: the tab follows, no F5.

    Args:
        page: The tab, on the home page.

    Returns:
        The review used and each round's time, in ms.
    """
    name = next((each for each in REVIEWS if page.evaluate(AVAILABLE_JS, each)), "")
    times: list[int] = []
    for _ in range(ROUNDS if name else 0):
        start = time.monotonic()
        page.evaluate(RUN_JS, name)
        page.wait_for_selector(PAGE_READY, timeout=STEP_MS)
        page.click(PAGE_READY)
        page.wait_for_selector(HOME_READY, state="attached", timeout=STEP_MS)
        page.wait_for_function("() => typeof onRun === 'function'", timeout=STEP_MS)
        times.append(round((time.monotonic() - start) * 1000))
    return {"review": name, "rounds_ms": times}


def main() -> None:
    """Walk the pages, write /shots/walk.json (Playwright: in its image only)."""
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    home = f"http://127.0.0.1:{sys.argv[1]}/"
    walk: dict[str, Any] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(home)
        page.wait_for_selector(HOME_READY, state="attached", timeout=STEP_MS)
        page.wait_for_function("() => typeof onRun === 'function'")
        walk["clicks_from"] = time.time()
        walk["search"] = open_from_home(page, "search")
        if page.evaluate("() => Boolean(BY_ID.browse)"):
            walk["browse"] = open_from_home(page, "browse")
        walk["clicks_until"] = time.time()
        walk["console"] = console_step(page)
        walk["own_server"] = own_server_rounds(page)
        browser.close()
    OUTPUT.write_text(json.dumps(walk, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
