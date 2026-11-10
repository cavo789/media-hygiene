# 0665 — Library page: actions grouped in a few menus, filters folded — fewer controls at once

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/pick_acting.html.j2`, `src/media_hygiene/review/templates/pick_bar.css.j2`, `src/media_hygiene/review/templates/pick_bar_panel.js.j2`, `src/media_hygiene/review/templates/slideshow_menu.html.j2`, `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/search/templates/search.html.j2`, `.claude/skills/photo-picking-pages/SKILL.md`, `tests/integration/tags/test_pick_pages.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The maintainer asks for sub-menus where relevant (Albums, Slideshow on `/library`). 0660
made *▶ Slideshow ▾*; the album panel (📚) and *🏷 Describe ▾* exist too, but each is built
its own way. *Measured* (the served `/library` of the demo tree parsed, 2026-11-10): **243**
controls (buttons, inputs, selects, `<details>`) and **14** `<dialog>` in one page; the left
column alone holds about 12 filter widgets and 6 `<details>`; line 2 of the bar holds 10
entries (move to an event, move to the month, take back, invert, set aside, ▶, order, size,
📚, 🏷).

Load the `photo-picking-pages` skill first: the bar is shared, so the change goes into the
`pick_*` templates and reaches every tile page.

## Proposal

- **One menu component** (`.barPanel`, keyboard: ↓ opens, arrows move, Esc closes, a letter
  per entry shown at its right) for every group of the bar, in this fixed order on every
  page: *📂 Move ▾* (to an event · to their month · to a folder), *📚 Album ▾* (add · take
  out · make from the results · prepare for sending · link), *▶ Slideshow ▾* (0660),
  *🏷 Describe ▾* (tag · date · place), then *Invert*, a gap, *🗑 Set aside*, *Apply now*.
  The page's most used action stays a plain primary button (`pick_first`).
- **Filters**: the three most used stay visible (words, dates, folder); the others go under
  *More filters ▾*, and an active one always shows as a chip on line 1 (0565), so nothing
  hidden narrows the results silently (rule: never act on what is not shown).
- **A budget, tested**: controls visible at load without opening anything ≤ a figure to set
  after the regrouping (estimated: about 25 instead of about 60 visible today — to count in
  headless Chromium, visible ≠ present).
- The skill's table gets the menu order; the ⌨ panel lists the letters.

## Acceptance

- [ ] The same menus, same order, on every tile page (the shared-parts test)
- [ ] Every action still reachable by its key; no action lost (a table old → new in the PR)
- [ ] The count of visible controls at load measured before / after, the cap in a test
- [ ] Docs EN + FR (`commands/library.md`); `docs_screenshots` should run

## Questions for the maintainer

- The grouping above, or another one? (Shown as a mock-up first, in the PR.)

## Where the user gains

Before: 243 controls in the page (measured), 10 entries on the bar's line 2. After: 4 menus
and 3 buttons at the same place on every page (estimated 60 → 25 visible controls).
