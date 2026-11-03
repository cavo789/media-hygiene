# 0539 — Disk space page: previews cache and quarantine, with their limits

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/`, `src/media_hygiene/actions/`, `src/media_hygiene/places/toml_edit.py`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

"If this feature is not shown in the web interface, it is as if it did not exist." Each setting
is placed **on the page where it acts**, next to its visible effect (no catch-all settings page),
saved with `places/toml_edit` (comments kept, atomic) and **read back from disk** before being
shown. Follows 0532 (folder roles); analysed in detail at implementation time.

## Wanted

Space taken by previews (`[cache] previews_max_gb`) and by the quarantine (`[clean]
purge_hint_days`), with *Empty* / *Purge* (purge needs the visual path of 0525 first, and the
Apply-now / undo rules). Reached from a home tile.

## Decided (2026-11-03, review of PR #61)

By the maintainer: the whole page now (previews cache **and** quarantine), since 0525 is DONE (`mh undo --pick`): its Purge part no longer waits.
