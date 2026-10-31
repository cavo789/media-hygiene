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
