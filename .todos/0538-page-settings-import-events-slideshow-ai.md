# 0538 — Settings on their pages: import steps, event grouping, slideshow speed, local AI, language

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/services/import_copies.py`, `src/media_hygiene/review/sort_*.py`, `src/media_hygiene/review/templates/`, `src/media_hygiene/places/toml_edit.py`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

"If this feature is not shown in the web interface, it is as if it did not exist." Each setting
is placed **on the page where it acts**, next to its visible effect (no catch-all settings page),
saved with `places/toml_edit` (comments kept, atomic) and **read back from disk** before being
shown. Follows 0532 (folder roles); analysed in detail at implementation time.

## Wanted

- Import page: `[imports] then` as checkboxes ("after the import: find copies, bursts…").
- Events page: "split / merge more" over `[classify] merge_gap_hours`, `min_event_size`,
  `trip_min_km`, with a preview of the events.
- TV slideshow: a speed button (`[slideshow] interval_seconds`).
- 🤖 Local AI state (`[classify.ai] url`, `model`): connected / absent, choice among the
  installed models (Ollama API listing: to check).
- A language picker in the bar (`[general] locale`).
- May split into one TODO per page at implementation.
