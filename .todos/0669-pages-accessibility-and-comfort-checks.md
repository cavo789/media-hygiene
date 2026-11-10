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
      with a reason
- [ ] Reduced motion honoured by the frame (slideshow cross-fade included)

## Where the user gains

Before: 1 page honours reduced motion (measured), no contrast / zoom check. After: every
page checked in CI.
