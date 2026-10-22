# 0305 — browse: one compact bar instead of the seven-line header

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/review/templates/review_side.css.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`, `tests/integration/tags/test_browse_page.py`

## Why

On `mh browse` (maintainer's screenshot, 2026-10-22, 1920×946 window), the sticky header
under the dark page bar stacks seven lines: the *Search by words* link, five selection
buttons, the status, the picking line, the album bar, its *No album yet* hint and the
safety sentence. The grid starts around y ≈ 300 (**estimated** from the screenshot), and
most buttons are greyed out while nothing is picked: space taken for nothing.

## What (layout agreed in chat, 2026-10-22)

One line above the grid, in the grid column (the tree column starts at the same height):

- **Nothing picked**: `C:\Photos\1999 — 6 files · nothing set aside` on the left,
  `Sort by [name ▾]` on the right.
- **Something picked**: the same line turns into an action bar on an accent background:
  `✕ 3 picked │ Set aside · Invert │ Album [____] + Add · Take out │ TV · Send`.
  `✕` is *Pick none*; *Take out of the set aside* shows only when a picked file is set
  aside already; the *No album yet* hint becomes the field's placeholder.
- *Search by words* becomes two tabs at the top of the left column: **Folders / Words**.
- The safety sentence (*Nothing is deleted from this page…*) moves to a 🔒 line at the
  bottom of the keys panel: always in sight, no height taken (product rule: the CLI and
  pages teach read-only 🔒 in one line).
- Status / errors (`#status`, `#chosen`, *Saving…*, *Nothing was saved*) go into the bar
  itself, the error in `--bad` as today; `apply_now.html.j2` stays reachable (below the bar
  when it shows).
- The keys panel at the bottom left is unchanged (the maintainer likes it; same as the
  other pages — see 0304).
- Narrow screen: the action bar may wrap on two lines; if it wraps more, group Album /
  TV / Send behind an `Album ▾` button.

`album_bar.html.j2` is shared with `review.html.j2` and `search.html.j2`: add a compact
variant (a parameter of the include) rather than change those two pages; check them
afterwards.

## Gain

Space above the grid ≈ 300 px → ≈ 95 px; grid height ≈ 650 → ≈ 850 px (**+30 %**), about
4.5 rows of thumbnails in sight instead of 3.5 (all **estimated** from the screenshot,
185 px per row). To measure after the change on the same window size.

## Done when

- Both states render as above; the keyboard shortcuts and the mouse rectangle still work;
  the sticky side column follows the new header height (`--head`).
- Tests of the page cover: the bar switching state on pick / unpick, *Take out* shown only
  with a set-aside file picked, the 🔒 line in the keys panel.
- Every new string through `_()`, `i18n_update`, French translated; `browse.md` updated in
  both languages; say that `docs_screenshots` should run (never run it unasked).
