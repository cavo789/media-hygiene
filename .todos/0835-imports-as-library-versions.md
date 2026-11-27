# 0835 — Each import is a version of the library: see its photos, undo it from the page

- **Priority**: Medium
- **Batch**: import
- **Depends**: none
- **Files**: `src/media_hygiene/services/import_run.py`, `src/media_hygiene/services/history_runs.py`, `src/media_hygiene/services/history_rows.py`, `src/media_hygiene/search/`, `src/media_hygiene/actions/copy_in.py`, `src/media_hygiene/cli/menu_catalog_import.py`, `documentation/en/commands/history.md`, `documentation/fr/commands/history.md`, `tests/unit/`
- **Needs maintainer**: the name shown for a version (date only, date + source folder, a label typed at import?)

## Idea (maintainer, 2026-11-15)

Like commits in a git history: every import creates a new version of the photo library.
One can see which photos came with which import (otherwise everything mixes), and go back:
cancel an import and remove its photos.

## What exists already (checked 2026-11-15)

- Every `import` is a journaled run (`services/import_run.py`, `actions/copy_in`): each copy
  written ahead and proven.
- `history` lists the runs; `undo <run>` removes an import's copies (the source is never touched).
- `import_end` reads the last import's day from the journal (`--since`).

## What is missing

1. **Seeing first** (rule 0524): a library filter "photos of this import" (from the run's
   journal: the copied destinations), so an import's photos are shown before anything else,
   and before an undo.
2. **A timeline page / tab**: the imports as versions, newest first (date, source, count,
   size, still present / moved by `sort` / set aside), each opening its photos in the library.
3. **Undo from the page**: *Undo this import* with the count it will touch, the shared
   confirmation, and what happens to photos moved since (`sort`, albums, renames by the user
   in Explorer): follow by content id, never by stale path; a photo already edited or tagged
   is listed, not silently removed.
4. Undoing an import that is not the last one: allowed (imports are independent copies), but
   say so; no "rewind" of later versions.

## Out of scope

Branches, diffs of edits, versioning of photo contents: the library stays plain folders.

## Acceptance

- Library filter by import, tested with the demo tree (two imports, one undone).
- Undo after a `sort` move removes the moved copy (test), and the index forgets it.
- Docs (en + fr), menu catalog entry, `.po` updated.
