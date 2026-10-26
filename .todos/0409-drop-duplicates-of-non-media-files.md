# 0409 — Drop duplicate search in non-media files (`[scan] extensions = [".pdf", …]`)

- **Priority**: Medium
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/filters.py`, `src/media_hygiene/config/scan_settings.py`, `src/media_hygiene/config/categories.py`, `src/media_hygiene/services/data_checks.py`, `src/media_hygiene/services/clean.py`, `src/media_hygiene/plan/models.py`, `src/media_hygiene/plan/pairs.py`, `src/media_hygiene/actions/clean.py`, `src/media_hygiene/actions/clean_gone.py`, `src/media_hygiene/actions/clean_step.py`, `src/media_hygiene/actions/sort_build.py`, `src/media_hygiene/actions/sort_moves.py`, `src/media_hygiene/report/group_views.py`, `src/media_hygiene/services/chosen_review.py`, `src/media_hygiene/services/places_index.py`, `tests/integration/test_other_files.py`, `documentation/en/commands/audit.md`, `documentation/fr/commands/audit.md`

## Why

The very first media-dedup also found copies of any file (`[scan] extensions` with `.pdf`,
`.docx`…: compared byte for byte, `MediaKind.OTHER`, software folders skipped, copies always
quarantined). media-hygiene is now a photo/video tool (visual facts, bursts, near
duplicates, classify/sort, places, faces): no page, guide or review handles these files, and
the maintainer decided (2026-10-26) the feature is no longer useful. It costs a kind in every
`match` on `MediaKind`, warnings in `data_checks`, a quarantine rule in `services/clean.py`, a
test file. Non-media files become "intruders" to report instead: 0410.

## What

- `[scan] extensions` and categories accept media extensions only (photos, RAW, videos): a
  non-media one is refused at load with a translated message naming it and pointing to 0410's
  report ("media-hygiene only handles photos and videos"). Keep restricting to a subset
  (`.jpg` only) — that is still useful.
- Remove `MediaKind.OTHER`, `ScanFilters.other_files`, `ScanSettings.other_files`,
  `APP_DIR_NAMES` skipping if nothing else needs it, the two warnings in `data_checks.py`, the
  quarantine reason in `services/clean.py`, the branches in `plan/`, `actions/`, `report/`.
- No backward compatibility: the maintainer is the only user (2026-10-26) and accepts the
  break. An old journal, report or index row with an `other` kind may be refused
  or skipped; no fixture, no release note.
- `i18n_update` (strings removed), docs EN + FR: remove the mention of other extensions.

## Check

`grep -rn "OTHER\b\|other_files" src` empty; `tests_quick --depth 1`, then `check` (a kind
removed is cross-cutting).
