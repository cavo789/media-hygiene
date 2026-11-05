# 0515 — Home page tiles open the page they count: a new "Intruder files" tile, Faces → `mh people`

- **Priority**: Medium
- **Batch**: intruders
- **Depends**: —
- **Files**: `src/media_hygiene/report/summary.py`, `src/media_hygiene/report/writer.py`, `src/media_hygiene/cli/home_tiles.py`, `src/media_hygiene/review/home_parts.py`, `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/review/templates/home_parts.css.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/clean/15-intruder-files.md`, `documentation/fr/clean/15-intruder-files.md`

## Reported (maintainer, 2026-10-30)

On the home page, the *Where you are* box ("Où vous en êtes") should show the total size of the
intruder files, and a click on it should open the `mh review --intruders` page.

## What exists already (read in the code, 2026-10-30)

- The tiles: `cli/home_tiles.py` builds 8 `HomeTile` (Last audit, Extra copies, Quarantine,
  Only on the NAS, Sort, Words, Faces, Backup); file at 161 lines.
- A tile is a `<button data-go="space">` (`home_draw.js.j2:124`): it only switches to a **space**
  of the page (Clean, History…), never opens a step's page.
- `ReportSummary` (`report/summary.py`) carries **no** intruder figure: the counts live only in
  the report (`findings.intruders` → `intruder_section`, `intruders.csv`). The home page reads
  `summary.json`, so it cannot know them today.
- The grid is `repeat(4, …)` (`home_parts.css.j2:221`), 2 columns on a phone: a 9th tile would
  sit alone on a third row.
- TODO 0509 point 2 wanted the count on the *action* "Set the intruder files aside"; this TODO
  replaces that point (0509 updated): a tile is where the user looks for figures.

## To do

1. `summary.json`: `intruder_files: int = 0`, `intruder_bytes: int = 0`, filled by the audit
   (protected and backup folders left out, as the page counts them, so the tile and the page
   agree). Older summaries load with 0 (`tests/fixtures/0.2.0/` keeps loading).
2. Tile *Intruder files*, after *Extra copies*: value = weight (`784 MB`), sub = "262 files —
   set them aside"; `Pill.TODO` when some, `Pill.NONE` when none ("None"), `—` before any
   audit. Not added to the Clean badge (0509: that one means copies).
3. Click target: `HomeTile` gains an optional `step: str | None` (an action id); when set,
   the tile opens that step like the action button does (`review-intruders`, same
   running/served-page path, way back home kept), else `data-go` as today. With no intruders,
   the tile goes to the Clean space instead (an empty page is useless).
   Same fix for **Faces** (maintainer, 2026-10-30: "20,614 faces found", clicked, landed on
   `#sort` instead of the `mh people` page): when faces were found, `step="people"`
   (`menu_catalog_sort.py`); none yet → the Sort space as today. Check every other tile the
   same way (does a single page show what the tile counts? Words → `search`?) and list the
   choice per tile in the commit.
4. Layout: 9 tiles, 3 columns × 3 rows on the PC, 2 on a phone (maintainer, 2026-10-30: yes).
5. Freshness: the figure is the last audit's; files set aside since (a clean of intruders)
   lower it only at the next audit. Proposed: after `review --intruders` applies, subtract
   what was moved (the run is in the journal) — or simply say "at the last audit" in the sub.
   Decide while implementing; the simple wording is acceptable.
6. `home_tiles.py` will pass 200 lines: move `_clean_tiles` into its own module first
   (`near_limit.sh`).
7. Tests: summary round-trip with and without the fields; tile value/sub/pill for none, some,
   no audit; the tile's `step` makes the button open `review-intruders`; old summary → 0.
8. Docs EN + FR `clean/15-intruder-files.md` (and the home page chapter if it lists the tiles):
   the tile leads to the page. `docs_screenshots` should then run — not run by the TODO.

Setting? No (`few-settings`): nothing to tune.
