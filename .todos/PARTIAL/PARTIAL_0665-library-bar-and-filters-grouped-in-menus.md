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

## Status — PARTIAL (2026-11-11)

### Done
- One menu component (`pick_bar_panel.js.j2`): ↓ on a summary opens, ↑ ↓ move, Esc closes and
  gives the focus back, the letter drawn at an entry's right (`data-key`) runs it; focus ring
  of 0669 kept (native summaries and buttons). Listed in the ⌨ panel.
- Line 2's fixed order from one list (`bar_menus`, `pick_bar.css.j2`): 📂 Move ▾ (search's
  `pick_first`, primary), 📚 Album ▾, ▶ Slideshow ▾ (moved from line 1 to line 2),
  🏷 Describe ▾, 🔀 Invert; gap; 🗑 Set aside, Apply now.
- Filters: words, dates, *Path contains* shown; album, Show, Sorted, Without, place under
  *More filters ▾* (open state in the URL, `?filters=more`); the album filter got its chip
  (the others had one, 0565).
- Old → new (no action lost, every key kept: the buttons keep their ids, keys call `.click()`):

  | Before (line 2) | After |
  |---|---|
  | 📂 Move to an event… (primary button) | 📂 Move ▾ → to an event… (E) |
  | 🗓 Move to their month… | 📂 Move ▾ → to their month… (M) |
  | ↩ Take out of the set aside | same place |
  | 🔀 Invert (I) | after the menus |
  | 🗑 Put aside (Delete) | same, right end |
  | ▶ Slideshow ▾ (line 1) | line 2, 3rd menu (H, T) |
  | 📚 Album ▾, ➕ | 2nd menu |
  | 🏷 Describe ▾ (tag, date, place) | 4th menu (T, D, P) |
  | Sort by, S M L | line 1 (view controls), unchanged |

- Visible controls at load on `/library`, *measured* from the served HTML
  (`tests/support/visible_controls.py`: not inside a closed `<details>`, `hidden`,
  `<dialog>`, `<template>`): **46 → 33**; cap 33 in `test_pick_pages.py`. Present in the
  page: 187 → 189; 17 `<dialog>` (the TODO's 243 / 14 came from another count).
- CI browser walk `tests/support/menu_walk.py` (Chromium `checkVisibility`, cap 40 estimated).
- Docs EN + FR `commands/library.md`; skill table with the menu order.

### Not done
- *to a folder* in Move ▾. **Reason:** no move-to-a-folder action exists on the page.
- *make from the results* / *link* in Album ▾: *📚 album of the results* stays in the left
  column. **Reason:** it acts on every file found, not the picking; moving it into the
  picking's menu needs the maintainer's choice.
- The grouping itself awaits the maintainer's review (the TODO's question, mock-up = the PR).
- The browser cap (40) is an estimate until the first CI run prints the real count.
- `docs_screenshots` should run (bar and left column changed).
