# 0405 — Sorting progress read from the disk: sorted, nothing special, left, and the folders left

- **Priority**: Medium
- **Batch**: sort
- **Depends**: 0401
- **Files**: `src/media_hygiene/services/sort_figures.py`, `src/media_hygiene/review/sort_progress.py`, `src/media_hygiene/cli/status_view.py`, `src/media_hygiene/cli/home_stage_lines.py`, `src/media_hygiene/index/listing.py`, `documentation/en/commands/status.md`, `documentation/fr/commands/status.md`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`

## Why

The maintainer's first fear (2026-10-25): "I want to follow what was done and what is
left". Today's progress (0398, `sort_progress`) reads the latest classify plan and the
journal: it moves with each `classify` (files sorted by an earlier plan become "in
place"), it does not see a move made in Explorer, and its "in place" mixes "already
where the plan puts it" with "no rule moves it". With 0401's convention the disk itself
says it, without plan or journal, and it still says it the day media-hygiene is gone:

| Where the file is | State |
|---|---|
| `YYYY/YYYY-MM/<name>` (and a stage below) | sorted into an event |
| directly in `YYYY/YYYY-MM` | looked at, nothing special |
| anywhere else (old folders, other family members' folders, a jumble) | left |

## What to do

1. A pure function: a host path (relative to a sort root) → sorted / nothing special /
   left, from the convention's shape (`YYYY/YYYY-MM`, the month consistent with the year,
   `00` allowed). Kept folders and protected folders (`config.toml`) are counted apart,
   never as "left".
2. The counts from the index alone (`index/listing`), no walk: `mh status` prints them
   (*Sorted: 62 % · nothing special: 9 % · left: 16,400 files in 214 folders*, example
   figures), the home page's *Sort* space too; `review-sort` keeps its plan-based line
   for the work of the current plan.
3. **The folders left**, the largest first, with their count and the one-liner that
   opens them in `review-sort` (or `search` with that folder as a filter): the work list.
   In `mh status`, the first ten; all of them on the page.
4. Docs (both languages): `status` and step 11 of the sort guide; `docs_screenshots`
   must then run.

## Tests

- The shape function: each row of the table, `00`, a month that does not match its year
  folder (`2009/2010-01`: left), a stage below the event.
- Counts from a synthetic index; kept and protected folders apart.
- A file moved in Explorer into the convention counts as sorted after the next audit.

## Status — PARTIAL (2026-10-26)

### Done
- The pure shape function (`classify/convention.shape_in`, read anywhere in the path) and its tests.
- Counts from the index alone (`services/sort_disk.py`), protected/backups/`leave` apart, cached
  per index version; measured 0.20 s for 70,000 paths.
- `mh status`: the line, the ten largest folders left, `mh search --folder "<folder>"` (new option).
- The home page's *Sort* space shows the disk figures; review-sort keeps its plan-based line.
- Docs (both languages): `status`, step 11, `search --folder`.

### Not done
- Every folder left listed **on a page** (only the first ten in `mh status`).
  **Reason:** the search page's *Not sorted yet* filter (0407) and `--folder` give the way to
  work through them; a dedicated list on the home page is a design choice for the maintainer.

## Closed (maintainer, 2026-10-26)

The list of every folder left is the search page with *Sorted: not sorted yet* (0407): no other
page is needed. DONE.
