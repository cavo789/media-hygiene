# 0427 — A paired phone may download originals and set photos aside, behind a setting

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan_paths.py`, `src/media_hygiene/config/`, `src/media_hygiene/config/templates/`, `src/media_hygiene/search/`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `documentation/en/reference-config.md`, `documentation/fr/reference-config.md`

## Why

Decided by the maintainer (2026-10-27, during the `/todo:iterate` lot of 0361): media-hygiene is
for anyone, but in this family a paired phone should be able to download a photo's original
(`/original/`) and *set aside* photos. Today `lan_paths.py` refuses both (preview size only;
every write stays the PC's).

## What

1. A `config.toml` setting under `[review]` (e.g. `lan_phone_writes = false`), **off by
   default**: a phone of an unknown home network gets nothing more than today.
2. On: `/original/` and the *set aside* `POST` of search/browse join the phone's explicit list
   (`phone_may`); the set-aside still goes through the PC's journal/quarantine (`mh` runs the
   write, as 0361 decides for page writes). Off: both answer 403 as today.
3. Tests for both values (a paired phone with the setting off: 403; on: the original served,
   the set-aside accepted); docs en + fr (`commands/home.md`, the config reference).

## Acceptance

- With the setting off nothing changes; with it on, a paired phone downloads an original and
  sets a photo aside, undoable from the PC.
