# 0348 — One search page: words first, the folder as a filter (Folders view to merge or drop)

- **Priority**: Low
- **Batch**: search
- **Depends**: 0347
- **Files**: `src/media_hygiene/review/templates/pick_views.html.j2`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/folder_tree.py`, `src/media_hygiene/services/search_pages.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`
- **Needs maintainer**: the choice between merging `browse` into `search` and keeping both (what merging loses, below)

## Context

Asked by the maintainer (2026-10-24):

1. Now: put *🔎 Words* first, *📁 Folders* second (`pick_views.html.j2`): words will be used more.
2. Then: since a search by words can be narrowed to a folder, could the *Folders* button go
   away — `/search` only, with a folder filter chosen from a drop-down list of the folders?

## What merging loses (to weigh before item 2)

- `browse` shows a folder **as it is**, every file in folder order, without typing anything —
  `search` needs words or a filter; an empty search must then mean *everything in the folder*.
- The folder tree (open/closed, counts per folder) is richer than a drop-down: tens of thousands
  of files in hundreds of folders do not fit a `<select>` — a typed filter with suggestions,
  or the tree itself in the left column.
- Links to `browse` from elsewhere (the home page, *Apply now* 0243, the docs, `mh browse`, the
  menu catalog) move or redirect; the `browse` command and its doc page.

## Proposal

Item 1 at once. For item 2: one page, the left column holds *Words* then the folder tree as a
filter (a click narrows to that folder, empty words list it whole) — `browse` becomes this page
opened with a folder, the command kept as an alias. Decide at review.

## Acceptance

- [ ] *Words* is the first button.
- [ ] Item 2 per the maintainer's choice; docs, menu catalog and nav kept consistent.

## Status — PARTIAL (2026-10-26)

The maintainer answered the question on 2026-10-26: the search page is to replace `browse` and
`review-sort`.

### Done
- *Words* first, *Folders* second on both pages.
- The search's left column: *In a folder*, the folder view's tree (one shared template); a click
  narrows the search to the folder and below, empty words list it whole; ✕ clears it.

### Not done
- `browse` merged into the search (the command an alias, its links moved: home page, menu
  catalog, docs, nav).
  **Reason:** it would lose *Heaviest files* and the *bit rate* order, which only the folder view
  has; bringing them into the search first, then retiring `browse` (and `review-sort`), is an
  order of work for the maintainer to choose at the review.

Follow-up (2026-10-26, maintainer: yes, bring them first): TODO 0408.

## Inbox (2026-10-27)

- Answered 2026-10-26; the rest is 0408 and its follow-up. Closed to DONE (2026-10-27).
