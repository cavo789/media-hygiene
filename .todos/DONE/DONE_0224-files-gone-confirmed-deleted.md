# 0224 — Files gone since the last audit (deleted in Explorer): the user confirms which were deleted on purpose, so that they are proposed again when they come back

- **Priority**: Medium
- **Batch**: journal
- **Depends**: 0216, 0203
- **Files**: `src/media_hygiene/index/pruning.py`, `src/media_hygiene/index/gone_rows.py` (new), `src/media_hygiene/services/audit.py`, `src/media_hygiene/cli/review_modes.py`, `src/media_hygiene/services/gone_reviewing.py` (new), `src/media_hygiene/review/gone_app.py` (new), `src/media_hygiene/review/gone_views.py` (new), `src/media_hygiene/review/templates/gone_review.html.j2` (new), `src/media_hygiene/review/templates/gone_review.js.j2` (new), `src/media_hygiene/report/gone_decisions.py` (new), `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/actions/remembered.py`, `src/media_hygiene/actions/clean_gone.py` (new), `src/media_hygiene/console/gone_view.py` (new), `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_gone_rows.py` (new), `tests/integration/test_gone_review.py` (new), `documentation/en/clean/09-undo-history-purge.md`, `documentation/fr/clean/09-undo-history-purge.md`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`

## Context

Chosen by the maintainer on 2026-10-17, after 0216 (photos set aside that come back) and 0223
(`browse`): removals should go through MH, but old habits stay — photos will still be deleted in
Explorer, and the tool knows nothing of them, so it cannot propose them again when a phone backup
brings them back.

The index can tell. After a walk, `index/pruning.py` forgets the files the walk proves gone (below
a folder mounted this time, readable, analysed), and `index/rematch.py` (0147) first recognises the
files moved or renamed in Explorer (same size, modification time and partial digest: their rows
follow). A file proven gone and not followed was deleted — or moved to a disk that is not plugged
in: only the user can tell, hence a confirmation. Measured on the maintainer's index (2026-10-17,
52,094 files): every file has its size and its partial digest (SHA-256 of its first and last
64 KiB), 21 % a full SHA-256, 97 % of the images their perceptual hashes.

## What to do

1. **Keep what is forgotten**: before `pruning` forgets a file proven gone that `rematch` did not
   follow, record it in a new index table (`index/gone_rows.py`): its path, size, modification
   time, partial digest, full digest when known, the day it was found gone. Not in `PATH_TABLES`
   (a gone file has no path to follow). `services/audit.py` (182/200) and `index/schema.py`
   (183/200) only call the new module.
2. **Say it**: the audit's *What you can do* block, when records wait: "312 photos and videos have
   disappeared since the last audit (deleted in Explorer?): say which ones you deleted on purpose,
   so that MH sets them aside if they come back: `mh review --gone`".
3. **`review --gone`**: the records grouped by folder and by day found gone; each with its preview
   when the preview cache still holds it, else its name, date, size and camera. Keys as the other
   reviews: `D` deleted on purpose, `M` moved elsewhere (forget it), `G` the whole folder, `U`
   undecided. Saved at once under a `gone` key of `decisions.json` (`report/gone_decisions.py`:
   `report/decisions.py` is full), read back and shown.
4. **`clean --decisions`** applies them: a journal mark per file deleted on purpose (a new kind
   without a file action, like `mark-album`, undone by `undo`), the records of both answers
   dropped; `history` counts the marks.
5. **0216's remembered set** includes those marks, matched on the full SHA-256 when both sides have
   one, else on size and partial digest (the audit computes the partial digest of every file whose
   size a remembered one has: it reads 128 KiB). A match then goes through 0216's straightforward
   path: listed apart, back to the quarantine with the next `clean`.
6. A record whose file reappears later (same size, mtime and partial digest at another path: a
   disk plugged in again) is dropped silently: it was moved.

## Explicit non-goals

- Remembering any deletion without the user's confirmation.
- Files outside the folders mounted at the audit.

## Acceptance

- Unit (`test_gone_rows.py`): a deleted file is recorded; a renamed folder (0147) records nothing;
  a folder not mounted records nothing; a file that reappears drops its record.
- Integration (`test_gone_review.py`): two audits around a deletion; `review --gone` saves `D` and
  `M`; `clean --decisions` writes the marks and drops the records; a copy of the deleted file put
  back under another name is proposed by the next audit (0216), the one answered `M` is not; `undo`
  of that clean removes the marks.
- Docs both languages: cleaning step 9 ("deleted in Explorer?"), the `review` command page; say in
  the report that `docs_screenshots` should run.

## Gain (estimated)

Photos deleted in Explorer become as recognisable as those set aside through MH, for one answer per
folder: when a phone backup brings them back, they are proposed again instead of being sorted and
cleaned a second time.
