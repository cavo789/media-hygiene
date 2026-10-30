# 0535 — What the audit analyses and ignores, shown and changed from the pages

- **Priority**: High
- **Batch**: one-interface
- **Depends**: 0532
- **Files**: `src/media_hygiene/services/audit.py`, `src/media_hygiene/review/`, `src/media_hygiene/places/toml_edit.py`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

"If this feature is not shown in the web interface, it is as if it did not exist." Each setting
is placed **on the page where it acts**, next to its visible effect (no catch-all settings page),
saved with `places/toml_edit` (comments kept, atomic) and **read back from disk** before being
shown. Follows 0532 (folder roles); analysed in detail at implementation time.

## Wanted

Home or audit page: "Analysed: photos, RAW, videos · ignored: …" from `[scan] extensions` and
`excluded_names`, with *Change* (categories as checkboxes, names as a list); a change makes the
last audit stale: say so and offer to re-run it.
