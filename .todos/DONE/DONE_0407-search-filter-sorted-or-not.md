# 0407 — search: filter the photos already sorted (`YYYY/YYYY-MM/…`) from the others

- **Priority**: High
- **Batch**: search
- **Depends**: 0403
- **Files**: `src/media_hygiene/classify/convention.py`, `src/media_hygiene/search/query.py`, `src/media_hygiene/search/views.py`, `src/media_hygiene/search/statements.py`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

Asked by the maintainer on 2026-10-26: the search page is to **replace `browse` and
`review-sort`** (that also answers the question of 0348). To sort with it, the user needs
to see **what is left to sort**: a filter that keeps the photos not sorted yet, or only the
sorted ones, then pick and move them (0403's *Move to an event…*).

With the convention of 0401, the path alone says it (`classify/convention.py`, 0405 reads
the same):

| Where the file is | Filter value |
|---|---|
| `YYYY/YYYY-MM/<name>` (and a stage below) | sorted, in an event |
| directly in `YYYY/YYYY-MM` | sorted, nothing special that month |
| anywhere else | not sorted yet |

## What to do

1. A **filter** on the search page, next to the years and the folder: *All* (default) ·
   *Not sorted yet* · *Sorted*. With *Sorted*, the user may want to tell "in an event" from
   "nothing special": decide while implementing whether that is a 4th value or not (keep it
   to 3 unless the page shows a need). Load the `photo-picking-pages` skill first: the
   filter bar is shared with the other tile pages.
2. Server side: `Filters.sorted` (an Enum, never a bare string), sent by `SearchAsked`, read in
   `statements.conditions` as an SQL condition on the path. The shape is read **from the
   path alone**, without plan or journal: a SQLite function registered on the search
   connection from `convention.shape_of`, or an equivalent `GLOB`/regex condition. Measure on
   a synthetic index of 70,000 rows (the maintainer's collection, measured 2026-09-28) that it
   costs less than ~50 ms per search; say the figure in the commit.
3. **Which root**: the convention reads `YYYY/YYYY-MM` below the sort root, but a photo of
   `C:\Photos\2009\2009-11\…` lies below `/data/c` too. Proposed: a pair of consecutive
   folders `YYYY` then `YYYY-MM` of the same year **anywhere** in the path counts (no root to
   know, the same answer for `C:\Photos` and `D:\Tri`); `shape_of` gets that reading, and 0405
   uses it too. Say it in the feedback if a real tree shows a false positive (a folder `2009`
   holding `2009-11` that is not a sorted tree).
4. The filter is kept in the page's URL/state like the others, and said in the line that
   describes the search (`views.py`: e.g. `… · not sorted yet`).
5. Docs (both languages): `commands/search.md`, the filter and the "pick, then *Move to an
   event…*" way of sorting; `docs_screenshots` must then run (do not run it here).

## Out of scope

- The move itself: 0403. The counts of what is left (`mh status`, the home page): 0405.
- Merging `browse` and `review-sort` into `search`: 0348 (its maintainer question is answered
  by this request: search replaces them; to update when 0348 is planned).

## Tests

- The shape read anywhere in the path: `C:\Photos\2009\2009-11\Tom\a.jpg` sorted,
  `C:\Photos\2009\2009-11\a.jpg` sorted (nothing special), `C:\Photos\2009\2010-01\a.jpg`
  and `C:\Photos\Novembre 2009\a.jpg` not sorted, `1985/1985-00` sorted.
- A search with *Not sorted yet* returns only the others; *All* is unchanged (equivalence
  with today's query on the same index).
- The filter combines with the words, the years and the folder.
- A file moved by 0403's *Move to an event…* leaves *Not sorted yet* at the next search
  (the index follows the move).
