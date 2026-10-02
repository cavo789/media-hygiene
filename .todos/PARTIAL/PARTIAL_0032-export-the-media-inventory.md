# 0032 — Export the media inventory to Excel from the index (no scan)

- **Priority**: Low
- **Batch**: report
- **Depends**: 0025, 0033
- **Files**: `src/media_hygiene/cli/cmd_inventory.py` (new), `src/media_hygiene/services/inventory.py` (new), `src/media_hygiene/report/inventory_workbook.py` (new), `src/media_hygiene/index/repository.py`, `src/media_hygiene/report/csv_export.py`, `pyproject.toml` (openpyxl), `documentation/en/`, `documentation/fr/`

## Context

The user wants **one Excel file listing every photo and video with everything the audit
learned about it**. Today nothing does that:
- `plan.csv` (report folder) lists only the files the plan acts on: duplicate groups, broken
  files, orphan sidecars. A file with no copy is absent.
- `summary.json` holds totals, not files.
- The index (`/cache/index.sqlite`) holds the facts, but a SQLite file is not a user deliverable.

After 0025, the index holds, for every media file:
- today: size, mtime, SHA-256, integrity (broken reason and detail), dimensions, sharpness,
  EXIF date, camera;
- added by 0025: date source, GPS, time zone, lens and exposure settings, format, JPEG quality,
  exposure stats; for videos: duration, codec, date and place from the tags.

That list serves needs not identified yet: statistics per camera or per year, finding the
blurry or tiny pictures, spotting a camera with a wrong clock. Writing it at every `audit`
would cost time for nothing. An on-demand export reads the index only and costs no scan.

The index must only list files that still exist: 0033 makes `audit` and `clean` remove the
rows of files that are gone, and records the date of the last complete walk of each root.

## Proposal

- `media-hygiene inventory` writes `inventory.xlsx` to a new report folder
  (`<reports>/<stamp>-inventory/`):
  - openpyxl in `write_only` mode (streams rows: 70,000 files must stay fast and small in
    memory); openpyxl comes with 0027, or with this TODO if it lands first;
  - sheet **Files**: one row per media file, frozen header row, autofilter, column widths;
    typed cells (numbers as numbers, dates as dates), so sorting and filtering work in any
    regional settings, unlike a CSV;
  - sheet **Summary**: counts per year, camera, format, kind, integrity, with / without date and
    GPS (same figures as the 0025 inventory block).
- `--format csv` writes `inventory.csv` instead, like `plan.csv` (BOM, `;` in French): reuse the
  helpers of `csv_export.py`.
- Columns: host path (`HostPathMapper`), folder, file name, kind, one column per fact of the
  index; plus **duplicate group** and **copies**, derived from the SHA-256 shared by several
  rows (free, no plan needed). The keep / delete verdict stays in the report's `plan.csv`: it
  depends on the settings of the run (protected, preferred folders).
- Derived labels (quality, exposure) computed at export time from configurable thresholds,
  never stored.
- The Summary sheet gives, per root, the date of its last complete audit (0033), so the reader
  knows how fresh the inventory is.
- It refuses to run on an empty or missing index, with a tip ("run `audit` first").
- Document that the SQLite index can also be opened read-only with any SQLite browser.

## Acceptance

- [ ] Export of a synthetic index: one row per media file, host paths, translated headers and
      sheet names, typed cells, frozen header and autofilter (read back with openpyxl in tests).
- [ ] Duplicate group and copies columns match the SHA-256 groups of the index.
- [ ] The Summary sheet shows the date of the last audit of each root.
- [ ] No file of `/data` is opened during the export (test with a counting fake).
- [ ] `--format csv` gives the same rows.
- [ ] Documentation en + fr (a screenshot of the workbook from the docs sample); `.po` translated.

## Status — PARTIAL (2026-10-02)

### Done
- `media-hygiene inventory [--format xlsx|csv]` (`cli/cmd_inventory.py`, `services/inventory.py`):
  reads `/cache/index.sqlite` only (`index/listing.py`), writes
  `<reports>/<stamp>-inventory/inventory.xlsx` (sheets Files and Summary, write-only streaming,
  typed cells, frozen header, autofilter, column widths) or `inventory.csv` (Files sheet, BOM,
  `;` and decimal comma in French).
- Columns: host path, folder, name, kind, size, mtime, date taken (as `classify` reads it), date
  source, year, time zone, camera, lens and exposure settings, flash, width/height, sharpness,
  format, JPEG quality, exposure measures, GPS, video tags, rating, software, integrity, decoder
  message, SHA-256, duplicate group, copies.
- Derived labels (Quality: blurry/small; Exposure: dark/bright) from new `[inventory]` thresholds
  in `config.toml`, computed at export time.
- Summary: last complete audit per root (`roots` table of 0033), then counts per kind, year,
  camera, format, integrity, with/without date, with/without GPS, duplicates.
- Refusals with a tip, no traceback: no `/cache` or no index (never created by the check), empty
  index, damaged index, no `/reports`.
- Tests: workbook read back with openpyxl, CSV same rows, translated headers and sheet names,
  no file of `/data` opened (data deleted + counting `open`), errors, CLI.
- Documentation en + fr: `reference-inventory.md` (includes the SQLite-browser note), commands,
  mount points, cache page; captures `inventory.txt` and `help-inventory.txt` regenerated.

### Not done
- A screenshot of the workbook from the docs sample.
  **Reason:** nothing in the devcontainer or the docs pipeline renders an `.xlsx` (no Excel,
  no LibreOffice); an HTML imitation of a spreadsheet would show something Excel does not.
  Same gap as PARTIAL 0027 (classify workbook). Maintainer decision: accept an HTML rendering of
  the first rows, add LibreOffice headless to the docs tooling, or take one real Excel capture by
  hand.
- The Summary sheet does not repeat the total video duration of the 0025 console block.
  **Reason:** left out to keep the sheet to file counts; one line to add in
  `report/inventory_summary.py` if wanted.
