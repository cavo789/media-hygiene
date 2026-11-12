# 0551 — One photo reference everywhere: `path` + content `id`, for `places/` and `people/`

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/config/place_photos.py`, `src/media_hygiene/places/config_photos.py`, `src/media_hygiene/classify/hand_placed.py`, `src/media_hygiene/config/people_settings.py`, `src/media_hygiene/config/people_files.py`, `src/media_hygiene/people/config_file.py`, `src/media_hygiene/people/followed.py`, `src/media_hygiene/people/known.py`, `src/media_hygiene/services/sort_links.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/config/templates/config.toml.j2`, `documentation/en/`, `documentation/fr/`

## Why

The maintainer, 2026-10-31: two ways of naming a photo exist and must become one.
`[[classify.place_photos]]` knows a photo by its content (`sha256` 64 hex + `size`, in
`config.toml`, unreadable with dozens of photos); `people/*.toml` by `<path>#<face>`, followed when
the tool moves a file (`follow_people`, `index.moves`) but lost when a folder is renamed in
Explorer. A path alone breaks on outside renames; a hash alone locks the data into media-hygiene
(the maintainer wants the files usable by another program later).

## What

- One entry form for both, in a file per place / per person beside `config.toml`:
  ```toml
  photos = [
      {path = 'C:\Photos\2024\2024-07-Geer\IMG_0096.JPG', id = "fc7749d8b88880b3:2484373"},
  ]
  faces = [
      {path = 'C:\Photos\…\IMG_0096.JPG', id = "fc7749d8b88880b3:2484373", face = 2},
  ]
  ```
- `id` = first 16 hex of the SHA-256 + `:` + size: what media-hygiene trusts. Collision odds for
  100 000 files ~3·10⁻¹⁰ (estimated: n²/2⁶⁵), lower with the size. The index holds the full
  SHA-256: the lookup reads no file.
- `path` = the real host path, kept current: at once by the tool's own moves (`sort`, `undo`,
  quarantine, search *Move to an event* — today's `follow_links`), and at the end of each `audit`
  for outside renames (the `id` finds the file, the `path` is rewritten). Atomic save, comments
  kept, read back.
- `config.toml` keeps the place (name, circle/OSM area) and a link `file = "places/<name>.toml"`,
  like `people/` (0300).
- Old forms (`sha256`+`size`+`path`; `<path>#<n>`) still load and are rewritten at the next save.
- An edited photo is another photo (maintainer, 2026-10-31): it loses its place (falls back to its
  GPS) and its face names.
- Tests, per event: `sort`, `undo`, quarantine and back, Explorer rename then `audit`, copy to
  another drive, edited copy, two identical copies (tie broken by name).

## Status — PARTIAL (2026-11-02)

### Done
- Places: photos in `/config/places/<name>.toml` as `{path, id}` (`id` = 16 hex of SHA-256 + `:` + size); `[[classify.place_photos]]` keeps `place` + `file`; atomic save, comments kept, read back; old `sha256`+`size` form loads and migrates at next save.
- Shared helper `src/media_hygiene/config/photo_ref.py` (`PhotoRef`, `content_id`, `follow_paths`, `relocate`, `ref_line`, `write_refs`); tool moves follow via `follow_links` (`services/sort_links_places.py`); `audit` relocates Explorer renames by id (`services/photo_refs_audit.py`).
- Tests per event in `tests/unit/test_photo_ref.py` (sort, undo, quarantine and back, Explorer rename, copy to another drive, edited copy, identical copies tie by name).
- Docs `commands/places.md` en + fr.

### Not done
- People faces as `{path, id, face}` in `people/*.toml` (still `<path>#<n>`), old form migration, relocation at audit.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  **Reason:** faces are `<container>#<n>` strings throughout `people/`; saving needs the index to compute ids; `people/person_files.py` (182 lines) and `people/config_file.py` (194) need new modules. Reuse `config/photo_ref.py`.
- Relocation only runs at the end of the `audit` command, not in `import` nor the home-page audit.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  **Reason:** decision for the maintainer.
- Wire change: the places page's take-back request sends `id` instead of `sha256` — to confirm.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)

### Decided (2026-11-02)
- The places page's take-back sends `id`: kept.
- Relocation after `import` and the home page's audit too → TODO 0570 (with the people half).

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
