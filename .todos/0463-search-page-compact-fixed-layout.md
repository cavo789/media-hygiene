# 0463 — Search page: more room for photos, every control at a fixed place

- **Priority**: High — the search page is the centre of media-hygiene
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/review/templates/pick_acting.html.j2`, `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/search/templates/pick_order.html.j2`, `src/media_hygiene/review/templates/pick_keys.html.j2`, `src/media_hygiene/review/templates/pick_keys_more.html.j2`, `src/media_hygiene/search/file_card.py`

## Why

The maintainer, 2026-10-29, on a 1920 px screenshot: the action band takes 4 lines, controls move
with the width (*Show* jumps from line 1 to line 2), the ⌨ panel takes ~10 lines (*More keys*
pushes the search form out of sight), the **Search** button is below the fold, a card is ≈ 640 px
for ≈ 170 px of photo (estimated from the screenshot). Load skill `photo-picking-pages` first:
the `pick_*` templates are shared.

## Golden rule (decided)

The screen never jumps: no control appears or disappears with the selection, the results or a
message. Disable instead, reserve room (fixed widths, `min-height`), long text in a tooltip.

## What (decided with the maintainer)

1. Top band = 2 fixed lines (CSS grid, no wrap). Line 1: counter (fixed width) · 📺 On the TV ·
   Sort by · thumbnail size S/M/L (`localStorage`). Line 2: actions on the selection, always
   shown, compact (emoji + short word, full label in tooltip), disabled while nothing is picked:
   album field + ➕ ➖ · 📺 Share · ✉️ Send · 📂 Event… · then *🗑 N set aside (size)* (path in tooltip)
   + **✅ Apply** (was *Apply now*).
2. Every button has an emoji; every button with a key says it in its tooltip (`Invert (I)`).
3. Left panel: *Show* (all / 📷 / 🎬) and *Sorted* (all / sorted / not yet) as segmented controls.
   Drop the *Words from* select; keep the ability as query syntax (`folder:`, `name:`,
   `"exact phrase"`), documented.
4. Dates: one line, narrow fields (~11ch) + a 📅 ▾ menu (today / month / year / clear).
5. 🔍 Search sticky at the bottom of the form; `/` focuses Words, Enter searches.
6. Active filters as chips above the grid (« 3 filters · ✕ clear all »), line height reserved.
7. ⌨ panel: drop the 🔒 *Nothing moves without your GO…* line (→ Apply tooltip + help page);
   move `I` to *More keys*; *More keys* opens as a floating non-modal dialog (Esc closes).
8. Cards: caption on one line with ellipsis (full in `title` and the large view); tags 2 lines +
   `+N`. Size S: photo only; L: whole caption and tags.
9. Load on scroll instead of *Show more*.

## Acceptance

- At 1920 and 1280 px, picking, searching and applying leave the grid's `getBoundingClientRect`
  unchanged (test). Photos visible above the fold before/after: measured on `demo`.
- Same keys and layout on the other pick pages (skill's tests); i18n FR complete; docs EN/FR;
  say that `docs_screenshots` must run.
