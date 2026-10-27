# 0399 — One photo page instead of three: `search` takes in `browse` and `review-sort`

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0348, 0397, 0398
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/search/app.py`, `src/media_hygiene/services/search_app.py`, `src/media_hygiene/services/search_pages.py`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/services/sort_reviewing.py`, `src/media_hygiene/review/templates/pick_views.html.j2`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/review/home_views.py`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`
- **Needs maintainer**: the design of the merged page (which left-column views, what the bar holds when an event is shown), and whether `mh browse` / `mh review-sort` stay as aliases opening that page

## Why

Maintainer, 2026-10-25 (during the unattended run 0394–0398): "could `mh browse` (or `mh
search`) replace `mh review-sort`, i.e. remove that page and reuse an existing one? And maybe
remove `mh browse` too, keeping only `mh search`, or merge the two since both allow about the
same thing: analyse the differences and gather the features into one page instead of three."

0348 already asks for `browse` to become a view of `search` (words first, the folder tree as a
filter). This TODO extends it to `review-sort`, now that 0396 and 0397 bring onto `search` what
was review-sort's own: a period to the day, a date rule made or updated from the photos shown,
the group checked before → after and sorted with *GO*.

## What each page has today (read from the templates and the docs, 2026-10-25; to complete)

| Feature | search | browse | review-sort |
|---|---|---|---|
| Shared grid, picking, large view, bar (`pick_*`) | ✓ | ✓ | its own grid of an event's photos (to check against the skill `photo-picking-pages`) |
| What leads to the photos | words + filters (period, path, source) | folder tree, heaviest files, videos | the list of events of a classify plan (filters *to decide* / *one at a time*) |
| Set aside (`decisions.json`, `clean --decisions`) | ✓ | ✓ | — |
| Albums | ✓ | ✓ | — |
| People: a name taken off, *Why this name?* | ✓ | — | — |
| Sort by / Show (size, videos) | 0347 | ✓ | — |
| Name an event, choose its folder (`sort-decisions.json`) | — | — | ✓ |
| Rules: *Remember as a rule*, *Your rules* | 0396 (period → rule) | — | ✓ (0392, 0393, 0395) |
| *Sort this event now* / *GO* (moves files, journaled) | 0397 | — | ✓ (0390, 0397) |
| Progress of the sort (done / left, history) | — | — | 0398 |
| Needs | the index | the index | a classify run (`plan.json`) + the index |

## What

- A decision first (maintainer): the merged page's left column as views — *🔎 Words* (with the
  period), *📁 Folders* (0348), *🗂 Events* (the events of the latest classify run, its
  filters and progress, 0398) — and the right side always the same grid and bar; an event or a
  period shown offers the same panel *Check, then sort* (0397) and *📌 Make it a rule* (0396).
- Then: one server and one page (`/search`), the other routes redirect to it with the view
  chosen; `mh browse` and `mh review-sort` open that view (or are removed, as decided: memory
  "CLI only if useful in console").
- List every feature that would be lost or moved (keys of review-sort: N, S, U, R…, the
  workbook overlay, the event facts panel) and keep or drop each one, said in the feedback.

## Explicit NON-goals

- No change to `classify`, `sort`, the decision files' formats: the page reads and writes them
  as the three pages do today.

## Tests

`test_page_frame.py` and `test_pick_pages.py` for the one page; the old routes redirect; the
menu catalog and `COMMANDS_TOO` follow what is decided; say that `docs_screenshots` should run.

## Status — PARTIAL (2026-10-25)

### Done
- The differences, read from the templates and routes after 0394–0398 (2026-10-25):
  - **search and browse are already one server and one page family**: the same app
    (`search/app.py`), the tabs 🔎 Words · 📁 Folders (`pick_views`), the same `pick_*` grid,
    keys, large view and bar, the same set-aside (`decisions.json`) and albums. What differs:
    the left column (words + period + path + source vs the folder tree), *Sort by* / *Show*
    (browse only: 0347), the people's *Why this name?* (W) and the rule of a period with its GO
    (search only, 0396/0397), the heaviest files and videos (browse only). Merging them is 0348.
  - **review-sort is another server** (`review/sort_app.py`, its own session on the latest
    classify plan and workbook), opened alone by `mh review-sort` (the home page launches it as
    a step, not as a tab). Its own: the event list with 3 filters and the progress (0398), the
    Folder / Name fields and their live destination, O / S (send / leave picked photos), V and
    Shift+Z (sure proposals), M (sort now, 0397), R and *Your rules* (0392–0395), the workbook
    overlay and its conflicts. It has no set-aside, no albums, no people.
  - **One key would have two meanings**: Delete sets photos aside on search/browse, but takes
    back a choice on review-sort — the skill `photo-picking-pages` forbids a key with another
    meaning on another view.
- A proposal, cheapest first (estimated from the sizes: review-sort is ~15 modules and
  ~1,400 template lines, with ~10 integration test files):
  1. **search + browse → one page** (0348): `/search` with the tree as a filter of the left
     column; `mh browse` opens it on the Folders view. Nothing lost; ~1 session.
  2. **review-sort as a third view of that page** (🗂 Events): one server holding the index
     *and* the sort session; the bar shows Folder / Name / destination / GO when an event is
     shown. Lost or to decide: Delete's meaning, the workbook conflicts' banner, the server
     needing a classify run only for that view. ~3–5 sessions.
  3. Alternative to 2, without merging the servers: the same tabs on review-sort's page
     (🔎 · 📁 · 🗂) opening the other page on the same port when it is served by the home
     page — the user sees one page with three views; nothing is lost. ~1–2 sessions.

### Not done
- The merge itself (items 1, 2 or 3 above), the old routes' redirects, the menu catalog,
  `COMMANDS_TOO`, the docs of the three commands.
  **Reason:** the TODO's own *Needs maintainer*: which level of merge (1 only, 1 + 2, or
  1 + 3), what Delete means on the Events view, and whether `mh browse` / `mh review-sort`
  stay as entry points or go (memory "CLI only if useful in console"). Removing pages and
  commands the maintainer chose is a design change: listed here, asked, not guessed.

## Inbox (2026-10-27)

- Superseded by the decision of 2026-10-26 (0408): the search replaces `browse` and `review-sort` (level 1 + 2, review-sort as the *🗂 Events* view). Closed to UNNEEDED (2026-10-27).
