# 0215 — `search`: set aside the photos found (a person, a year, a word), applied by `clean --decisions`

- **Priority**: Medium
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/search/app.py`, `src/media_hygiene/search/fts.py`, `src/media_hygiene/search/views.py`, `src/media_hygiene/search/chosen.py` (new), `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/report/chosen_decisions.py` (new), `src/media_hygiene/report/decisions.py`, `src/media_hygiene/services/review.py`, `src/media_hygiene/plan/review.py`, `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/actions/reversal.py`, `src/media_hygiene/actions/clean.py`, `src/media_hygiene/cli/clean_confirm.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_search_set_aside.py` (new), `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `documentation/en/find/quick-guide.md`, `documentation/fr/find/quick-guide.md`, `documentation/en/clean/08-clean.md`, `documentation/fr/clean/08-clean.md`

## Context

Asked by the maintainer on 2026-10-17, with 0216: a user deletes every photo of someone (a former
partner, say), or photos and videos during a cleaning. Today the tool can find those
photos (`people` names a face, `search person:"…"` finds them, 0091) but cannot remove them: the
user deletes them in Explorer, and the tool knows nothing of it — so it cannot recognise them when
a phone backup brings them back months later (0216). Removing them through the tool makes the
removal journaled, undoable, and remembered.

## What to do

- The search page (`search/templates/search.html.j2`): select photos (a click or `Space` on a
  picture, "select all the files found" for every match of the search, not only those shown), then
  *Set aside*. The selection is saved at once under a `chosen` key of `decisions.json` (host path,
  size, mtime of each file, the search that found them), the other keys kept, read back and shown:
  "1,234 photos set aside: `mh clean --decisions` moves them to the quarantine".
- `clean --decisions` moves them to the quarantine under a new action kind (`quarantine-chosen`),
  journaled and undoable like the other set-asides; the question before cleaning says how many and
  their size, apart from the duplicates; a file changed since it was chosen (size or mtime) is left
  and said; a file of a protected folder is refused, as everywhere.
- The search page must check that the reports folder is writable before saving (as `review` does:
  `ensure_writable`).
- 0223 (`browse`, the folder view) reuses this selection and this saving: keep them in
  `search/chosen.py`, independent of how the files were listed.
- Size caps: `report/decisions.py` (200/200), `actions/clean.py` (200/200) and
  `actions/reversal.py` (193/200): the `chosen` model, the action and its reversal go to new
  modules.

## Explicit non-goals

- Deleting for good from the page: the quarantine, as everywhere; `purge` erases.
- A rule that removes every future photo of a person automatically: 0216 recognises the very same
  files coming back; a new photo of that person is a new photo.

## Acceptance

- Integration: a search, a selection saved and read back, "all the files found" beyond the page's
  240, the other keys of `decisions.json` kept, `clean --decisions` moves exactly the chosen files,
  a file changed since is left, `undo` puts them back.
- Docs both languages: the `search` page, the "Find in short" guide (find, then set aside), cleaning
  step 8 (`--decisions` also applies what was chosen in `search`). Say in the report that
  `docs_screenshots` should run.

## Gain (estimated)

Removing every photo of someone: finding them by name, then deleting them one folder at a time in
Explorer → one search, *select all*, *Set aside*, one `clean`; undoable, and remembered when the
same files come back (0216).
