# 0240 — Tags: the Google Photos Takeout `description` becomes searchable words (own source `takeout`)

- **Priority**: Low
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/tags/models.py`, `src/media_hygiene/tags/producers.py`, `src/media_hygiene/config/tags_settings.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_takeout_facts.py`, `documentation/en/reference-sidecars.md`, `documentation/fr/reference-sidecars.md`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`

## Context

Follows 0217 (PARTIAL): the Takeout `.json` already gives a date and a place to the photos
without one; its `description` (the caption the user typed in Google Photos,
`scan/takeout_facts.py`) is read into the `takeout` table but never searched.
`TagSource.CAPTION` cannot hold it: that source is rebuilt from the cached vision descriptions
per model, so a Takeout caption there would be dropped or duplicated by the next `describe`.
Decided by the maintainer (inbox, 2026-10-19): a source of its own.

## What to do

- `TagSource.TAKEOUT` (`tags/models.py`), next to `FOLDER`/`NAME`: the description's meaningful
  words (same normalisation, plurals and stop words as `FOLDER`), and the sentence kept whole
  for the search as `CAPTION` keeps the model's. Produced in `tags/producers.py` from the
  index's `takeout` row, recomputed independently like every source; nothing when the
  description is empty.
- Never touched by `describe`; not written to XMP by default (`XMP_SOURCES` unchanged: it
  came from Google, the user can add it) — to say in the docs.
- Changing a `.json` (a new Takeout) changes the words at the next `tags` run: test it.

## Acceptance

- Unit: a Takeout photo with a description is found by a word of it; `describe` run after
  keeps it; an empty description gives nothing.
- Docs both languages: the Takeout section of `reference-sidecars.md`, the sources of
  `reference-tags.md`.

## Gain (estimated)

The captions typed in Google Photos over years, searchable without Ollama: 0 → every described
photo of a Takeout.
