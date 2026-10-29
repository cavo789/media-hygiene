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

## Status — PARTIAL (2026-10-29)

### Done
- Bar = two fixed lines (`search.html.j2`: flex with a `::before` break and `order`): line 1 where
  you are (ellipsis) · 📺 · Sort by · S/M/L (`localStorage` `mh-search-size`); line 2 the actions
  always shown, greyed while nothing is picked (`pick_grid.js.j2` disables `unpick`/`setAside`/
  `invert`), album ➕ ➖ 📺 Share ✉️ Send (`album_short` in `album_bar.html.j2`), 📂 Event…, the
  set aside line, ✅ Apply (`apply_short`, `apply_more` in `apply_now.html.j2`; hidden = greyed in
  place). The album's said lines float under the bar (absolute), never push the grid.
- Emojis on the pick buttons (🗑 ↩ 🔀) and keys in their tooltips (shared `pick_acting.html.j2`).
- Left column: Show (All/📷/🎬) and Sorted (All/sorted/not yet) segmented (hidden inputs keep
  `$("kind")`/`$("sorting")`); *Words of* select gone, `folder:`/`name:` syntax documented in the
  page help and the docs; `pick_order.html.j2` `order_kind = false`.
- Dates on one line + 📅 ▾ menu (Today/Month/Year/✕ Clear); 🔍 Search sticky at the form's bottom.
- ⌨ panel: no 🔒 line on search (→ Apply tooltip, docs); I moved to *More keys* (all pages);
  *More keys* floats over the page, Esc closes it (`page_frame.html.j2`, `keys.css.j2`).
- Cards: name/folder/caption one line with ellipsis + `title`; words max 2 lines, then `+N`
  (6 shown); S = photo only, L = everything.
- Load on scroll (IntersectionObserver on `#moreLine`, the button kept for the keyboard).
- Tests: `tests/unit/test_search_fixed_bar.py`; docs EN/FR `commands/search.md`, `status.md`.

### Not done
- Item 6, active filters as chips above the grid (« 3 filters · ✕ clear all »).
  **Reason:** the frame's contract allows nothing between the bar and the grid; it needs a place
  decided (a third bar line, or in line 1 next to the count) — left for a follow-up.
- Acceptance test in headless Chromium (grid `getBoundingClientRect` unchanged at 1920/1280 when
  picking, searching, applying) and the photos-above-the-fold count on `demo`.
  **Reason:** needs the `mddoc-playwright` image run; not done in this unattended run.
- `docs_screenshots` must run (search page captures are stale).
