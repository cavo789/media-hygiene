# 0428 — Intruder files: the page that picks them (checkboxes by extension and folder)

- **Priority**: Medium
- **Batch**: scan
- **Depends**: 0410
- **Files**: `src/media_hygiene/review/`, `src/media_hygiene/cli/cmd_review.py`, `src/media_hygiene/services/intruder_pick.py`, `src/media_hygiene/cli/audit_intruders.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `documentation/en/clean/`, `documentation/fr/clean/`

## Why

0410 (PARTIAL) counts the intruder files (zip, docx, pdf… in the photo folders), says so at
the audit's end, lists them in the report (`🧹 Intruder files`, `intruders.csv`) and has the
service that sets the files picked aside: `services/intruder_pick.set_intruders_aside(runtime,
IntruderPick(extensions, folders))` writes them into the `chosen` key of `decisions.json`
(`found_by = "intruder"`), so `clean --decisions` quarantines them per drive, journaled,
`undo`-able, and skips one moved or changed since (tested in
`tests/integration/test_intruders.py`). What is missing is the way the user picks: the
maintainer decided (2026-10-26) a page listing the intruders by extension and by folder, with
checkboxes (no tiles: skill `photo-picking-pages` does not apply), in the shared page frame.

## What

- A page (e.g. `review --intruders`, or a home-page action): `GET` lists
  `current_intruders(runtime)` tallied per extension and per folder (host paths, counts,
  bytes); `POST` (JSON) with the extensions and folders ticked calls `set_intruders_aside`
  and answers with the `chosen` key read back from the disk (product rule: a save is proven
  by reading it back).
- The audit's 🧹 line then leads to it with the single 👉 line when nothing else is next.
- Docs EN + FR: a step in `clean/` and the command page; `docs_screenshots` to run.
- Wording: `chosen_files` says "files chosen in 'search'"; say "intruder files" for
  `found_by == "intruder"`.
