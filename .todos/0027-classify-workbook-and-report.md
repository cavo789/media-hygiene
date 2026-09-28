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
  path, size, mtime, date and its source, event, proposal, band, reason, score.
- **`classify.xlsx`** (openpyxl) is only the editing surface.
- **`report.html`** shows thumbnails per category and band, reusing `report/thumbnails.py`.

**Sheets**:

| Sheet | One row per | Editable cells |
|---|---|---|
| Summary | — | none (counts per year, band, category, reason, date source) |
| Categories | proposed category | new name; "confirm the to-check files" (yes/no) |
| Events | event (span, count, folders, proposal, sample file names) | category |
| Files | media file | final folder (relative to the target root) |

- Precedence when applying: file > event > category.
- A human edit counts as sure: the file leaves the "to check" band.
- The Events sheet is where trips get their name ("Italie 2023") when GPS is missing, which is
  the common case (0026). One edit covers a few hundred photos.

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

**Decided 2026-09-28**: all three editing levels (Categories, Events, Files) are kept. The
"confirm the to-check files" column on the Categories sheet stays as proposed: it confirms a whole
"to check" category at once, instead of editing each of its rows.

## Acceptance

- [ ] Round trip: write, read back the editable cells, apply precedence; unit tests on a
      synthetic plan.
- [ ] Opens cleanly in Excel and LibreOffice (manual check noted in the commit).
- [ ] 70,000 rows written in seconds; measure and note the time. Check whether openpyxl's
      `write_only` mode keeps cell protection and data validation before relying on it.
- [ ] HTML report with thumbnails per category and band; documentation en + fr (screenshots via
      `docs_screenshots`, synthetic pictures only); `.po` translated.
