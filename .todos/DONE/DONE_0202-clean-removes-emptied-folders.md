# 0202 — `clean` removes the folders it leaves empty, as `sort` does (undoable)

- **Priority**: Medium
- **Batch**: actions
- **Depends**: —
- **Files**: `src/media_hygiene/actions/clean.py`, `src/media_hygiene/actions/clean_folders.py` (new), `src/media_hygiene/actions/sort_folders.py`, `src/media_hygiene/actions/sort_cleanup.py`, `src/media_hygiene/actions/outcome.py`, `src/media_hygiene/services/clean.py`, `src/media_hygiene/services/sort_report.py`, `src/media_hygiene/cli/cmd_clean.py`, `src/media_hygiene/cli/clean_confirm.py`, `src/media_hygiene/console/tables.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_clean_folders.py` (new), `documentation/en/commands/clean.md`, `documentation/fr/commands/clean.md`, `documentation/en/clean/08-clean.md`, `documentation/fr/clean/08-clean.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal A5). After a `clean`, a folder whose files were
all copies stays in Explorer, empty or holding only `Thumbs.db`. The report already badges such a
folder pair "entirely a copy: holds nothing else" (`PairEvidence.complete`). Czkawka, among
others, lists empty folders.

`sort` removes the source folders it empties (`actions/sort_folders.py` and
`actions/sort_cleanup.py`): deepest first; junk files (`[sort] junk_names`) set aside to the
quarantine first; roots, mount points and protected folders never removed; each removal journaled
(`REMOVE_FOLDER`), and `undo` recreates the folder (`Reversal.RECREATE_FOLDER`). `clean` does not
(checked on 2026-10-17: only `services/sort.py` uses `FolderCleaner`).

## Design (proposed 2026-10-17, the same as `sort`)

- Always, without an option: decided by the maintainer on 2026-10-17 ("I see no point in keeping
  empty folders"). `sort` keeps its own `--keep-empty-folders`.
- Candidates: the folders of the files this run moved or deleted (copies, near and burst shots,
  broken and empty files, orphan sidecars), and their parents up to a root.
- Never removed: mount points and roots (the folders given), the data dir, protected folders and
  everything under them. Excluded and skipped folders are entries, so their parents are never
  empty for this walk. A folder that was already empty before the run is not a candidate.
- Junk: the same `[sort] junk_names` setting (its comment in `config.toml.j2` says `clean` uses it
  too), set aside to the quarantine first. With `--delete` and no quarantine mounted, a folder
  holding junk stays (`Fate.HOLDS_JUNK`).
- One journaled sequence: the folder step runs last, in the run's own `JournaledChanges`, so
  `undo` recreates the folders before it puts the files back. Skipped when the run was stopped
  (Ctrl+C), as `sort` does.
- The question before cleaning says how many folders will be left empty and removed (the
  prediction of `verdicts(…, gone=…)`, as `sort`); the summary and `history` say how many were.

## What to do

- Size caps: `actions/clean.py` (200/200) and `console/tables.py` (200/200) are full. First move
  `_handle_broken` and `_quarantine_orphan` out of `clean.py` (a new module), then give the folder
  step the run's `JournaledChanges` (a property or a final hook), reusing `FolderCleaner`,
  `candidates`, `verdicts` and `FolderRules`; the new console lines go to a new module.
- Build the rules like `services/sort_report.folder_rules` (stops: data dir, roots, mount points;
  kept: protected folders): share one builder rather than copying it.

## Explicit non-goals

- No change to which files `clean` acts on.
- Folders empty before the run stay.

## Acceptance

- Integration (`tests/integration/test_clean_folders.py`): a folder of copies is removed after
  `clean`, its `Thumbs.db` in the quarantine; its parent too when it is left empty; a root, a mount
  point and a protected folder never; `undo` recreates the
  folders and puts every file back in them; a run stopped by Ctrl+C removes no folder; `--delete`
  without a quarantine keeps a folder holding junk.
- The question, the summary and `history` say the counts, in both languages.
- Docs both languages: `clean` command page, cleaning step 8. The console output changes: say in
  the report that `docs_screenshots` should run.
- Commit gate; the `cache-invalidation-reviewer` agent is not needed (no cache change).

## Gain (estimated)

After a clean, the folders made only of copies (the report's "entirely a copy" pairs) disappear
from Explorer instead of staying empty. Nothing to count on the maintainer's collection, already
cleaned (2 such folders left, measured on 2026-10-17).
