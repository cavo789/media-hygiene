"""Comfort checked in Chromium on a page of the frame (0669), both themes.

Run in the Playwright image by `tests/e2e/test_ask_dialog_browser.py`:
`python comfort_walk.py <page.html>`. Four checks: Tab reaches every visible
control with a visible focus ring; text contrast at least 4.5:1 from the computed
styles; at 1366x768 and at 200 % zoom no horizontal scroll and the bar on at most
two lines; with reduced motion no transition or animation longer than 0.2 s.
Exits 1 with the reasons. The image runs Python 3.10: nothing newer here.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from playwright.sync_api import Page

MIN_CONTRAST: Final = 4.5
MAX_MOTION_S: Final = 0.2
SIZES: Final = ((1366, 768), (683, 384))  # the screen, then 200 % zoom of it
CONTROLS: Final = (
    "a[href], button:not(:disabled), input:not([type=hidden]):not(:disabled),"
    " select:not(:disabled), textarea:not(:disabled), summary, [tabindex='0']"
)
# Each visible control, in the page, that a Tab press can reach.
VISIBLE_JS: Final = (
    "(sel) => [...document.querySelectorAll(sel)].filter((e) => {"
    " const r = e.getBoundingClientRect(); const s = getComputedStyle(e);"
    " return r.width > 0 && r.height > 0 && s.visibility !== 'hidden'"
    " && !e.closest('[hidden], [inert], dialog:not([open])') && e.tabIndex >= 0; })"
    ".map((e) => e.outerHTML.slice(0, 60))"
)
RING_JS: Final = """() => {
  const e = document.activeElement; const s = getComputedStyle(e);
  const ring = s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0;
  return { html: e.outerHTML.slice(0, 60), seen: ring || s.boxShadow !== 'none',
           target: e.tagName === 'BODY' };
}"""
CONTRAST_JS: Final = """(min) => {
  const parse = (c) => (c.match(/[\\d.]+/g) || []).map(Number);
  const lum = ([r, g, b]) => [r, g, b].map((v) => { v /= 255;
    return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); })
    .reduce((s, v, i) => s + v * [.2126, .7152, .0722][i], 0);
  const backdrop = (el) => { for (let e = el; e; e = e.parentElement) {
    const [r, g, b, a = 1] = parse(getComputedStyle(e).backgroundColor);
    if (a === 1) return [r, g, b]; }
    return [255, 255, 255]; };
  const bad = [];
  for (const el of document.body.querySelectorAll('*')) {
    const own = [...el.childNodes]
      .some((n) => n.nodeType === 3 && n.textContent.trim());
    const box = el.getBoundingClientRect(); const s = getComputedStyle(el);
    if (!own || !box.width || s.visibility === 'hidden' || el.closest('[hidden]')
        || el.matches(':disabled') || s.backgroundImage !== 'none') continue;
    const [r, g, b, a = 1] = parse(s.color); if (a < 1) continue;
    const back = backdrop(el); const [x, y] = [lum([r, g, b]), lum(back)];
    const ratio = (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
    if (ratio < min) bad.push([el.tagName, ratio.toFixed(2),
      el.textContent.trim().slice(0, 30)].join(' '));
  }
  return bad;
}"""
SCROLL_JS: Final = "() => document.documentElement.scrollWidth - window.innerWidth"
# A row is a band of the bar: a part starting above the bottom of the band before
# it is on that band (a short text centred beside a taller button starts lower).
BAR_ROWS_JS: Final = """() => {
  const bar = document.getElementById('bar'); if (!bar) return 0;
  const boxes = [...bar.children].filter((e) => e.offsetHeight)
    .map((e) => e.getBoundingClientRect()).sort((a, b) => a.top - b.top);
  let rows = 0; let bottom = -Infinity;
  for (const box of boxes) {
    if (box.top >= bottom) rows += 1;
    bottom = Math.max(bottom, box.bottom); }
  return rows; }"""
# Two frames: with reduced motion every property still transitions for .01 ms, so
# the ring read in the frame of the key press is its start (0 px), not what is seen.
SETTLE_JS: Final = (
    "() => new Promise((done) =>"
    " requestAnimationFrame(() => requestAnimationFrame(done)))"
)
MOTION_JS: Final = """(max) => [...document.querySelectorAll('*')].filter((e) => {
  const s = getComputedStyle(e);
  return [s.transitionDuration, s.animationDuration].some((list) =>
    list.split(',').some((d) => parseFloat(d) > max)); })
  .map((e) => e.tagName + '#' + e.id)"""


def _tab(page: Page) -> list[str]:
    """Press Tab through the page: every visible control focused, with a ring."""
    errors: list[str] = []
    wanted = page.evaluate(VISIBLE_JS, CONTROLS)
    reached: set[str] = set()
    for _ in range(len(wanted) + 5):
        page.keyboard.press("Tab")
        page.evaluate(SETTLE_JS)
        ring = page.evaluate(RING_JS)
        if ring["target"]:
            continue
        reached.add(ring["html"])
        if not ring["seen"]:
            errors.append(f"no visible focus: {ring['html']}")
    errors.extend(f"Tab skips {html}" for html in wanted if html not in reached)
    return errors


def _check(page: Page, theme: str) -> list[str]:
    """Run the four checks on the page in one theme."""
    errors: list[str] = []
    page.emulate_media(color_scheme=theme, reduced_motion="reduce")
    errors.extend(_tab(page))
    errors.extend(
        f"contrast {line}" for line in page.evaluate(CONTRAST_JS, MIN_CONTRAST)
    )
    for width, height in SIZES:
        page.set_viewport_size({"width": width, "height": height})
        if page.evaluate(SCROLL_JS) > 0:
            errors.append(f"horizontal scroll at {width} px")
        if page.evaluate(BAR_ROWS_JS) > 2:  # the bar's two lines
            errors.append(f"the bar needs more than two lines at {width} px")
    errors.extend(
        f"motion over 0.2 s: {el}" for el in page.evaluate(MOTION_JS, MAX_MOTION_S)
    )
    return [f"[{theme}] {error}" for error in errors]


def _both_themes(html: str) -> list[str]:
    """Open the page once per theme and gather what the checks found."""
    # pylint: disable-next=import-error,import-outside-toplevel
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    found: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for theme in ("light", "dark"):
            page = browser.new_context(
                viewport={"width": SIZES[0][0], "height": SIZES[0][1]}
            ).new_page()
            page.set_content(html)
            found += _check(page, theme)
        browser.close()
    return found


def main() -> int:
    """Check the page given as argument in both themes.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    problems = _both_themes(Path(sys.argv[1]).read_text("utf-8"))
    sys.stdout.write("".join(f"{line}\n" for line in problems))
    return int(bool(problems))


if __name__ == "__main__":
    sys.exit(main())
