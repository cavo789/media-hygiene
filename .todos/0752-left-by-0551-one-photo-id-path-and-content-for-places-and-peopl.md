# 0752 — What 0551 left: One photo reference everywhere: `path` + content `id`, for `places/` and `people/`

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `.todos/DONE/0551-one-photo-id-path-and-content-for-places-and-people.md`, `src/media_hygiene/config/place_photos.py`, `src/media_hygiene/places/config_photos.py`, `src/media_hygiene/classify/hand_placed.py`, `src/media_hygiene/config/people_settings.py`, `src/media_hygiene/config/people_files.py`, `src/media_hygiene/people/config_file.py`

Split from section 0551 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0551-one-photo-id-path-and-content-for-places-and-people.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- People faces as `{path, id, face}` in `people/*.toml` (still `<path>#<n>`), old form migration, relocation at audit.
- Relocation only runs at the end of the `audit` command, not in `import` nor the home-page audit.
- Wire change: the places page's take-back request sends `id` instead of `sha256` — to confirm.

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
