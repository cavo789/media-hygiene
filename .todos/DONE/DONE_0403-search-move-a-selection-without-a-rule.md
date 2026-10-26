# 0403 — search: move a selection to an event folder without a rule; source folders shown, the user's named ones unticked

- **Priority**: High
- **Batch**: search
- **Depends**: 0401, 0402
- **Files**: `src/media_hygiene/search/rule_desk.py`, `src/media_hygiene/search/rule_go.py`, `src/media_hygiene/search/rule_shown.py`, `src/media_hygiene/services/group_sort.py`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search_rule.js.j2`, `src/media_hygiene/review/templates/rule_dialog.html.j2`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

Found with the maintainer on 2026-10-25 (their journal `20261025-204417`, read through a
read-only mount): a `date_range` rule for 28/11/2009, sorted from the search page, moved
40 files from three folders: 24 from `Prints jan10` (right), 13 from the user's own
`Novembre 2009\Saint Nicolas 2009` (wrong: a second event that evening) and 3 from
`2010\Scans sep10`. The 30 photos of the user's own `Novembre 2009\Anniversaire
Tom` did not move: an older `path` rule listed first took them. The page greyed them
with the other rule's name; the user did not see that they would stay, and believed the
files had been copied to two places.

Decided with the maintainer:

- A rule taking files **from several source folders** must say so before the GO, with
  one tick box per source folder.
- **A selection with exceptions is a move, not a rule.** Once a photo or a folder is
  unticked, the rule no longer says what was done: saved, it would propose the unticked
  files again at every `classify`. *Save the rule* is then disabled, with the reason.
- The maintainer leans to **no `date_range` rule at all** for one-off events: search a
  period, pick, move. Once in a named folder, `existing_folder` keeps the files there
  (0404); only files arriving later for those days are not caught, and a search finds them.

## What to do

1. On the search page, **Move to an event…** for the chosen files (and for a period, with
   no rule): a name field (0401: a name only, the final `YYYY\YYYY-MM\<name>` shown,
   month of the earliest chosen file per 0400).
2. **Proposed destination first**: the user's named folder holding most of the chosen
   files (e.g. `…\Anniversaire Tom`, with its new place under the convention), never a
   second folder of the same name next to it.
3. Before the GO, the files grouped **by source folder**, one tick box each, with their
   count: a folder the user named with **another** meaning (`Saint Nicolas 2009`) is
   **unticked by default**; generic folders, other family members' folders and loose files are
   ticked.
4. *Make it a rule*: allowed only while nothing is unticked; otherwise disabled, with
   "you left N files aside: this is a move, not a rule".
5. The photos of the period another rule keeps: said in words above the grid ("30 photos
   of these days stay with the rule 'Anniversaire de Tom 2009'"), not only greyed.
6. The move is the same journaled sort as today (`group_sort`): undo line, read back.

## Tests

- Three source folders, one named otherwise: unticked by default; the GO moves the others.
- Unticking a file disables *Save the rule*; ticking it back enables it.
- The proposed destination is the user's folder holding most files.

## Decided (maintainer, 2026-10-25): "named with another meaning"

**By its dates**, no word list: a source folder with a meaningful name whose own files form
**one event** (one moment) is an event of the user's → unticked when it is not the
destination. A folder spanning several events or months (`Prints jan10`, `Scans sep10`, a
jumble) is a batch → ticked. The same predicate as 0404 case 8 (engine), one function.
