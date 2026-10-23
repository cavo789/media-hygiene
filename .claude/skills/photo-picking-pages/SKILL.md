---
name: photo-picking-pages
description: media-hygiene's contract for every HTML page where photos or videos are shown as tiles and picked (browse, search, the phone page, the review pages, any new one) — one layout, one way to pick (click, Ctrl, Shift, rectangle, Ctrl+A, invert), the same keys, the same large view, the same bar, built from the shared `pick_*` templates. Load it before creating or changing such a page, or a TODO that adds one.
disable-model-invocation: false
---

# Pages of photos to pick — one model for every page

The maintainer's rule (2026-10-23): every HTML page of the tool where photos can be picked
**must** look and work the same — same layout, same keyboard shortcuts where they apply, same
navigation, same way to pick photos. A user who learnt `browse` must not have to learn another
page. A page that differs is a bug, even if each page works on its own: the reports that led
here were "on `search`, a click picks without Ctrl, Shift+click and Ctrl+A do nothing" and
"`mh phone` has no double click to see a photo large".

## The shared templates (`src/media_hygiene/review/templates/`)

Any package's pages reach them (`i18n/templates.py`: the package's `templates/`, then these).

| Template | What it holds |
|---|---|
| `pick_grid.css.j2` | The whole look: left column (`review_side.css.j2`), the one bar, the tiles, ☑, rectangle, label; includes `pick_viewer.css.j2` |
| `pick_views.html.j2` | The tabs on top of the left column (📁 Folders · 🔎 Words); `pick_view` names the page |
| `pick_keys.html.j2` | The ⌨ panel at the bottom of the left column, its *More keys*, the 🔒 "nothing is deleted" line; `pick_all` says what Ctrl+A picks |
| `pick_acting.html.j2` | The start of the bar: where you are, or once something is picked ✕, the count, *Pick all N found*, *Set aside*, *Take out*, *Invert*; the saved line; *Apply now* |
| `pick_viewer.html.j2` | The large view and its `?` list of keys |
| `pick_grid.js.j2` | State, gestures, the bar, the saving (`CHOSEN_PATH`), the grid's keys; starts the strict mode, so it is included **first** |
| `pick_viewer.js.j2` | The large view's keys (`VIEWER_KEYS`) and its saves |
| `pick_band.js.j2` | The mouse rectangle |

A page includes them, then its own script (`browse.js.j2`, `search.js.j2`, `phone_review.js.j2`) that defines `TEXTS`,
`CHOSEN_PATH`, `card(file, index)` (it builds the picture and text, then `return wireCard(node,
index)`), `scope()` (what the files shown are, sent with every save) and `reopen(again)` (list them
again; `showFiles(listed, again)` keeps the cards when the files are the same). `files[i]` carries
at least `key`, `name`, `preview`, `original`, `chosen`, optionally `video`, `date`, `size`,
`facts`, `where`/`folder`.

## The contract

**Layout.** `page_header.html.j2` on top. Left column: the tabs, then what leads to the photos (a
folder tree, a search form, a list of groups), then ⌨ keys. Right: **one** sticky bar, then the
grid. Nothing else above the grid: no line of hints (they go in the keys panel or a
`<details>`), no second header. The album field always has its own line in the bar, and both lines
keep their height whether something is picked or not: **the grid never moves** when a pick starts
(otherwise a rectangle misses what is under the mouse — measured on `search`, 2026-10-23).

**Picking** (as in Windows Explorer) — all of them, on every page:

| Gesture | Effect |
|---|---|
| click | picks this file only (a second click on the only one picked unpicks it) |
| ☑ box · Ctrl+click | adds or takes out one file |
| Shift+click | every file from the last one clicked (Ctrl+Shift adds the range) |
| drag on the grid | a rectangle: every file it touches (Ctrl keeps what was picked) |
| Ctrl+A | every file shown (a page showing the first N of more: then *Pick all N found* in the bar) |
| I · *Invert the picking* | the others instead |
| arrows, Home/End | move the frame; Space picks or unpicks the framed file |
| Delete | sets the picked files aside |
| Enter · double click | the large view |

**Large view**: ← → previous/next, Home/End, Delete sets aside then the next one, Backspace takes
back, Space plays a video, F full screen, I its facts, A to the album typed, ? every key, Esc closes.

**Keys never fire while typing** in a field (`INPUT`, `SELECT`): Ctrl+A selects the text there. A
page with a search field sends the keys to the grid after Enter (the field loses the focus) and
lists `/` to come back (`pick_search_key`).

**Saving**: each choice saved at once, read back from the disk and shown (never "Saved" from
memory); the cards stay in place after a save (`relabel`). *Apply now* in the bar when the page was
opened from the home page.

## When a page needs something else

- Another meaning of a pick (the phone page, `phone_review.*`: ticked = leaves the phone): the
  gestures still only *pick*; the bar's two buttons act on the picking. The page sets, after the
  shared scripts: `saveChoice(action, keys)` (saves, reads back, says; true once saved — then
  `choose()` and the large view call `reopen(true)`), `placeCards(cards)` (the cards in groups,
  e.g. one per folder) and `deleteKeySets = false`; in the templates `pick_add`/`pick_remove`
  (the bar's buttons), `pick_marks = false` (no Delete, ⌫, A), `pick_space`/`pick_space_opened`
  (Space in the large view), `pick_mark`, `pick_safe`. A file that needs a confirmation is never
  changed with others (rectangle, Ctrl+A, invert, Shift then the button): alone only, after it;
  say "N left unticked" (TODO 0314).
- The phone page's exceptions, decided in 0314: no Delete key (its only deletion, for real, is
  the red button: "Delete" must not mean anything else there); in its large view Space ticks or
  unticks the file shown (it shows the PC's copy as a picture, never a video to play).
- A key that does not apply (no album on a page): leave it out of the panel and of `?`, never give
  it another meaning.
- A new gesture or key: add it to the shared templates, so every page gets it, and to this table.

## Checklist before declaring a page done

1. It includes the `pick_*` templates; no copy of their code (`tests/integration/tags/test_pick_pages.py`
   counts each shared part once per page — add the new page there).
2. Every gesture of the table works, checked in headless Chromium with a mocked API: the
   `mddoc-playwright` image (`docker create … python3 -u /w/drive.py`, `docker cp` the rendered page
   and the script in, `docker start`, `docker wait`, then `docker logs`: `start -a` shows nothing here),
   no `pageerror`, the grid's top the same before and after a pick.
3. Its documentation page describes the gestures in the words of `documentation/*/commands/browse.md`,
   both languages; say that `docs_screenshots` should run.
4. When filing a TODO for a page of tiles, name this skill and the gestures it must offer.
