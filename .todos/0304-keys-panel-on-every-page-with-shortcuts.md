# 0304 — The keyboard panel at the bottom left, on every page that has shortcuts

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/review_side.css.j2`, `src/media_hygiene/review/templates/keys.css.j2` (new), `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/near_review.html.j2`, `src/media_hygiene/review/templates/unwanted_review.html.j2`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/review/templates/gone_review.html.j2`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/`, `documentation/fr/commands/`

## Why

The maintainer, 2026-10-22, while cleaning their daughters' childhood photos in `browse`: they
did not know about Shift+click or Space. The keys were listed in a line of text under the
buttons, which they had not read. The review pages show them in a **⌨ Keyboard** panel at the
bottom of the left column, always in sight (`review_side.css.j2`), and that is the one they
know. Their request: the same look on every page where it is justified.

Done on 2026-10-22 for `browse`: the panel under the tree, plus **Invert the picking** (I), a
☑ box on each thumbnail and the mouse rectangle (`browse_band.js.j2`). This TODO covers the
other pages.

## Inventory (read on 2026-10-22: `keydown` in the templates)

| Page | Keys handled | Today | To do |
|---|---|---|---|
| `review` (bursts), `review --near`, `--junk`, `--pairs`, `--gone` | many | panel `#keys` | the shared style only |
| `browse` | many | panel (done) | the shared style only |
| `review-sort` (`sort_review.html.j2`) | Enter, N, P, U, V, Shift+S, ←/→, Space, O, S, Delete, Z, E, C, Esc | a line of 12 `<kbd>` at the bottom, all in one paragraph | **the panel**: the 4–6 most used in sight, the rest under **More keys** |
| `search` | arrows, Space, Enter, Delete, `/`, Esc, ←/→ in the viewer | no list | **the panel** (same picking as `browse`). Also the ☑ boxes and **Invert**? To decide: same grid, so likely yes |
| shared album (`share/album.js.j2`) | ←/→, Esc in the viewer | none | not justified: viewer only, read by the family; a tooltip at most |
| `people`, `places`, `home`, slideshow | Esc/Enter in fields, the TV remote | — | not justified (`home` already has its keys dialog) |

## What

- One shared style: `kbd` is styled in 8 templates (counted, `grep 'kbd {'`). Move it and the
  `#keys` panel rules into `keys.css.j2`, included by `review_side.css.j2` and by the pages that
  have no left column.
- A page without a left column (`review-sort`): the panel at the bottom left, fixed
  (`position: fixed`), foldable to its title so it never hides a photo; folded or not
  remembered per viewer (`localStorage`, wrapped in try/catch).
- Phone width (< 760 px): the panel goes under the content, as `review_side.css.j2` does already.
- Keep each page's own keys: this TODO moves where they are shown, not what they do.

## Tests

Per page touched: the rendered page holds `id="keys"` with its main keys, and no longer the old
line of text.

## Docs

The command pages that mention the keys (`review-sort`, `search`) in both languages. The pages
change: `docs_screenshots` should run afterwards (not unasked).
