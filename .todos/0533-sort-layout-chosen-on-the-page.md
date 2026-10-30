# 0533 — Sort target and layout chosen on the sort page, with a tree preview

- **Priority**: High
- **Batch**: one-interface
- **Depends**: 0532
- **Files**: `src/media_hygiene/review/sort_*.py`, `src/media_hygiene/classify/`, `src/media_hygiene/places/toml_edit.py`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

"If this feature is not shown in the web interface, it is as if it did not exist." Each setting
is placed **on the page where it acts**, next to its visible effect (no catch-all settings page),
saved with `places/toml_edit` (comments kept, atomic) and **read back from disk** before being
shown. Follows 0532 (folder roles); analysed in detail at implementation time.

## Wanted

- `[classify] target` picked with a folder chooser; `layout` (and `unsure_`, `manual_`,
  `undated_`, `received_layout`) chosen among named models, each with a **preview of the
  resulting tree on the user's own photos** (link with 0526, sort trial on a sample).
- `[classify] leave` and `person_folders` set from the folder menu of 0532.
