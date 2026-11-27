# 0820 — Library: stale filter chips pile up (three "not yet sorted", a day and a period at once)

- **Priority**: High
- **Batch**: library
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search_chips.js.j2`, `tests/unit/` (the library chips test), `tests/e2e/` or the page's browser test if one drives the chips

Reported by the maintainer on 2026-11-14 (screenshot, `/library?filters=more`, 39 769 files):
the chips line showed *pas encore triées* three times, `2007-12-31` twice and
`2007-01-01 → 2007-12-31`, while the left panel had **no** active filter (dates empty,
*Rangé* = *Tout*). Clicking a chip's ✕ ran a search (loader shown) but the chip stayed.
A single day and a period cannot both be active: there is one `from`/`to` pair.

## Cause (read from the code, not yet reproduced in a browser)

`showChips` replaces only `chipsLine`'s children; the chips folded into `+N` live in
`chipsFolded` and are **not** cleared. `foldChips` then starts with
`chipsLine.append(...chipsFolded.children)`, moving the old search's folded chips back onto
the line. Each search with more chips than fit adds its folded ones again: stale chips
accumulate. Their `off()` closures reset fields that are already empty, so ✕ searches again
and changes nothing; the stale chip is then re-appended once more. The screenshot's `+6`
fits this.

## Proposal

- `showChips`: `chipsFolded.replaceChildren()` before (or instead of relying on)
  `foldChips`'s re-append; or `foldChips` re-appends folded chips only when called by the
  `ResizeObserver` (a re-measure of the same set), never after a new set is drawn.
- Check that the chips shown always equal `activeFilters(asked)`: no duplicate text.

## Tests

- A test of the page's script (the existing chips test, or a jsdom/browser one) that: runs
  a search with many filters (forcing `+N`), then a search with none → zero chips, `+N`
  hidden; then the same with one filter removed → exactly the remaining chips once.
- ✕ on a folded chip (in the `+N` panel) removes it and nothing else.

## Done when

Searching, removing filters and resizing never shows a chip that is not in the left panel's
current state, and never the same chip twice.

## Status — DONE (2026-11-27)

`showChips` empties the `+N` panel before drawing the new set; unit test on the rendered script (not run in a browser).
