# 0027 — `classify` output: `plan.json`, a structure-locked Excel workbook, an HTML report

- **Priority**: High
- **Batch**: classify
- **Depends**: 0026
- **Files**: `src/media_dedup/classify/workbook/` (new: writer, reader, validation), `src/media_dedup/report/writer.py`, `src/media_dedup/report/templates/`, `src/media_dedup/constants.py`, `pyproject.toml` (openpyxl), `documentation/en/`, `documentation/fr/`

## Context

The proposal of 0026 must be reviewed and corrected by a person before anything moves. Excel
(or LibreOffice) is the editing surface. The user must **not** be able to break the file's
structure by accident, and `sort` (0028) must detect it when they do. Excel is good for mass
renames and poor for *seeing* photos, hence an HTML report with thumbnails next to it.

## Proposal

Written to `<reports>/<stamp>-classify/`:
- **`plan.json`** is the source of truth. It is versioned pydantic and holds every row: id, host
  path, size, mtime, SHA-256, date and its source, event, proposal, band, reason, score.
  - The proposal is a **target folder and a target name** (the original name for now): a
    renaming pattern (`2016-07-14_1530_IMG_1234.jpg`) could come later without a format change.
  - Ids are **stable across runs**: file ids from the content identity, event ids from 0026.
    0036 relies on them to carry edits over.
- **`classify.xlsx`** (openpyxl) is only the editing surface.
- **`report.html`** is where the user *looks* (see below), reusing `report/thumbnails.py`.

**Sheets**:

| Sheet | One row per | Editable cells |
|---|---|---|
| Summary | — | none: progress (files in place), counts per year, band, category, reason, date source, the work left |
| Categories | proposed category | new name; "confirm the to-check files" (yes/no) |
| Events | event (span, count, folders, proposal, sample file names) | name (for `{event}`), category |
| Files | media file | final folder (relative to the target root) |

- Precedence when applying: file > event > category.
- A human edit counts as sure: the file leaves the "to check" band.
- **"Stay where it is"** is a value of the drop-downs (translated) at every level: principle 3
  of 0026.
- Every sheet has a free **Notes** column, editable and ignored by `sort`: people annotate.
- The Events sheet is where trips get their name ("Italie 2023") when GPS is missing, which is
  the common case (0026). One edit covers a few hundred photos.
- **The Events sheet is a work list, ordered by the time it saves**: undecided events first,
  largest first, with a column "share of the files to check, cumulated". The decided events
  (existing folder, in place) come last. Naming the first rows covers most of the collection.
- Under sheet protection Excel cannot sort locked cells (filtering works): the sheets come
  pre-sorted in their most useful order, and `sort` matches rows by id, not by position.

**Structure lock**:
- The workbook structure is protected: no sheet can be renamed, moved, deleted or added.
- Every sheet is protected; only the editable cells are unlocked; auto-filter stays allowed.
- Editable cells use the Text number format, so Excel does not turn `2021` or `1/2` into a
  number or a date.
- A drop-down lists the categories without blocking free text.
- A `veryHidden` `_meta` sheet holds the format version, the plan id (matching `plan.json`) and
  a fingerprint of the locked content.
- Protection is a guard-rail against slips, not security: `sort` validates everything anyway
  (0028).

**Report**, the eyes of the workbook:
- Organised **by event**, with the ids and the order of the Events sheet, so that the user goes
  back and forth between the two windows. Each event shows its span, count, folders, proposal,
  reason, and up to 8 thumbnails spread over its span; a link opens all of them.
- One page per year (70,000 thumbnails do not fit one page), an index page with the progress
  and the work left.
- A **proposed tree**: the target folders with their file counts, "what the collection will look
  like", before anything moves.

**Decided 2026-09-28**: all three editing levels (Categories, Events, Files) are kept. The
"confirm the to-check files" column on the Categories sheet stays as proposed: it confirms a whole
"to check" category at once, instead of editing each of its rows.

## Acceptance

- [ ] Round trip: write, read back the editable cells, apply precedence; unit tests on a
      synthetic plan.
- [ ] Opens cleanly in Excel and LibreOffice (manual check noted in the commit).
- [ ] 70,000 rows written in seconds; measure and note the time. Check whether openpyxl's
      `write_only` mode keeps cell protection and data validation before relying on it.
- [ ] HTML report by event (same ids and order as the Events sheet), one page per year, the
      proposed tree; sort guide en + fr (screenshots via `docs_screenshots`, synthetic pictures
      only); `.po` translated.
