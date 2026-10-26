# 0406 — The pages that sort show the line "Links updated, read back from the disk"

- **Priority**: Low
- **Batch**: sort
- **Depends**: —
- **Files**: `src/media_hygiene/services/sort_event.py`, `src/media_hygiene/services/group_sort.py`, `src/media_hygiene/services/sort_links.py`, `src/media_hygiene/review/templates/sort_review.js.j2`, `src/media_hygiene/search/templates/search_rule.js.j2`

## Why

0382 made `sort` and `undo` rewrite the user's files that name photos by path (people's faces,
`albums.json`, `decisions.json`, `shrink-decisions.json`) and say it in one line, read back from
the disk. The CLI (`sort`, `undo`) shows that line; the pages that sort (*Sort this event now* in
`review-sort`, the GO of `search`) do the rewrite (it runs in `SortService.execute`) but do not
show it, nor a file that could not be rewritten. Product rule: a save is shown, read back.

## What to do

1. `SortedNow` (`sort_event`) and the group-sort answer (`group_sort`) carry `result.links`
   (lines and problems).
2. The page shows them under its "sorted" line, a problem as a warning.

## Tests

- The page's answer after a sort holds the links line when a name, an album or a decision moved.
- A broken `albums.json`: the answer holds the problem line, the sort is done.
