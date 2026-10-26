# 0410 — Intruder files in photo folders: report them, quarantine those the user picks

- **Priority**: Medium
- **Batch**: scan
- **Depends**: 0409
- **Files**: `src/media_hygiene/scan/walker.py`, `src/media_hygiene/scan/listing.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/report/`, `src/media_hygiene/services/clean.py`, `src/media_hygiene/cli/cmd_clean.py`, `documentation/en/clean/`, `documentation/fr/clean/`

## Why

The maintainer found zip, docx, xlsx, pdf… copied among the family photos (2026-10-26). The
walk already `scandir`s every entry and the index keeps each folder's full listing with sizes
(`walker._read` / `_fresh`, then `sort_entries` drops non-media): today these files are seen,
then ignored without a word. Telling the user costs no extra disk read (estimated from the
code: the counts come from listings already in memory or in the index).

## What

1. **Count**: while sorting a folder's entries, also tally files that are neither media nor
   a sidecar/companion (`.xmp`, `.aae`, Takeout `.json`, `.thm`, `Thumbs.db`, `desktop.ini`,
   `.DS_Store`…: never intruders): per extension, count and bytes, per folder. Reused listings
   give the same tally (one test: fresh walk vs. index-reused walk, equal).
2. **Audit end**: one line, e.g. `🧹 312 files that are not photos or videos (zip, docx,
   pdf…) take 4.2 GB in your photo folders`, then the single 👉 line leads to the step below.
   Nothing when there are none.
3. **Report**: an "Intruder files" section — totals per extension, heaviest folders, the
   full list in a CSV next to `plan.csv`.
4. **Clean**: the user chooses, never automatic (a docx may matter): by extension and/or
   folder. Chosen files go to the **quarantine** (per drive, `QuarantineRoute`), journaled,
   `undo`-able, never in a `protected` folder, never in an `excluded` one (not walked anyway).
   Intruder files moved by the user since the audit: skipped and said, like other clean
   steps.
5. **Docs** EN + FR: a new step in `clean/` (screenshots: say `docs_screenshots` should run),
   `commands/clean.md`; `i18n_update`.

## Questions (maintainer)

- Pick by CLI (`clean --intruders .zip,.docx`, `--intruders-in <folder>`) or a page listing
  extensions/folders with checkboxes (then skill `photo-picking-pages` does not apply: no
  tiles)?
- Should the sidecar/companion list be a setting? Proposed: a constant (few-settings rule),
  unless a collection needs its own.

## Decided (2026-10-26)

By the maintainer, at the start of `/todo:iterate`:

- Picking: a page listing the intruders by extension and by folder, with checkboxes (no tiles:
  skill `photo-picking-pages` does not apply); the shape of the page frame stays the shared one.
- Companions/sidecars: a `config.toml` setting (`[scan] companions = [...]`), with today's list
  as its default.
