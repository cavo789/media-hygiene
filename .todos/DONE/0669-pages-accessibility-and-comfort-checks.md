# 0669 — Accessibility and comfort checked on every page: motion, focus, contrast, zoom

- **Priority**: Low
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/page_frame.css.j2`, `src/media_hygiene/review/templates/pick_grid.css.j2`, `src/media_hygiene/review/templates/theme.css.j2`, `tests/support/pages_browser.py`, `tests/support/pages_walk.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

*Measured* (2026-11-10, `grep`): `prefers-reduced-motion` is honoured by the home page only
(`home_parts.css.j2`, `home.js.j2`); `aria-live` / `role="status"` appear in 50 places, so
the base is there. Nothing checks, page by page, what a family user with weaker eyes or a
laptop at 150 % zoom meets: focus ring visible on every control (menus included), contrast
of the muted texts in both themes, a bar that does not overflow at 125–200 % zoom or on a
1366-pixel screen, every control reachable by Tab.

## Proposal

- In the browser walk of CI (`pages_walk.py`): per page and per theme, (1) Tab through every
  visible control — none skipped, focus visible; (2) contrast of text ≥ 4.5:1 computed from
  the styles; (3) at 1366×768 and at 200 % zoom, no horizontal scroll and the bar on its two
  lines; (4) with reduced motion, no animation longer than 0.2 s.
- Fixes go in the shared CSS (`page_frame.css.j2`, `theme.css.j2`), never page by page.
- No new dependency if the four checks are written with Playwright's own API (to check:
  whether `axe-core` may be vendored for the CI image only — not the shipped image).

## Acceptance

- [ ] The four checks run on every page of the walk, both themes; failures fixed or listed
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
      with a reason
- [ ] Reduced motion honoured by the frame (slideshow cross-fade included)
  → code work, not the maintainer's: listed in 0718 (2026-11-12)

## Where the user gains

Before: 1 page honours reduced motion (measured), no contrast / zoom check. After: every
page checked in CI.

## Status — PARTIAL (2026-11-11)

### Done
- Static checks, `tests/unit/test_theme_comfort.py`: WCAG contrast of 26 text/background
  pairs of the tokens in both themes (computed from `assets/theme/tokens.css`), a
  `:focus-visible` ring in the shared `theme.css.j2` (and for the tiles in `pick_grid.css.j2`),
  a `prefers-reduced-motion` rule on `*` (transitions, animations, the slideshow's
  cross-fade) in `theme.css.j2`, and the rendered pages carrying them.
- Found and fixed in the shared CSS: light `--ok` text 4.28:1 on the page background
  (`--mk-tip-line` #5b7b36 → #52702f, 4.98:1); white text on the danger red in dark theme
  3.11:1 (danger button, badges: `--mk-on-danger`); tiles hid their focus (`outline: none`);
  only the home page and the busy pieces honoured reduced motion (now every page).
- Browser walk written, `tests/support/comfort_walk.py` (Playwright's own API, no axe-core, no
  new dependency): Tab reaches every visible control with a ring, computed-style contrast,
  no horizontal scroll and a bar on at most two lines at 1366x768 and 683x384 (200 % zoom),
  no transition or animation over 0.2 s under reduced motion; both themes. Run by
  `test_a_page_is_comfortable_in_both_themes` on the purge and people pages.

### Not done
- The browser run itself (no Playwright in the devcontainer): CI will tell whether Tab,
  → browser check: CI's job (headless Chromium), not the maintainer's (2026-11-12)
  the computed contrast (muted texts over photos, `.length`/`.badge` overlays), the zoom and the
  two-line bar hold; the script was never executed.
  **Reason:** Chromium is CI-only; first CI run may need fixes to the script.
- `pages_walk.py` (the home-server walk) does not run these checks yet; only two pages are
  → browser check: CI's job (headless Chromium), not the maintainer's (2026-11-12)
  covered. **Reason:** pages need data; extend with the pages it reaches once the first run is green.
- `axe-core` not vendored. **Reason:** the four checks fit Playwright's API; vendoring is optional.
  → browser check: CI's job (headless Chromium), not the maintainer's (2026-11-12)
- Light `--mk-primary` on `--mk-n-50` is 4.42:1 (outline buttons on sunken chips): not
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  fixed, no such use found statically.

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
