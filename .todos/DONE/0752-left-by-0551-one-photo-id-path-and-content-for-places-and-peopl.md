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

## Status — DONE (2026-11-13)

Each item checked against the code: all three were already done, only unticked.
- Faces as `{path, id, face}`, old `<path>#<n>` migration, relocation at audit: done by 0570
  (`config/face_refs.py`, `services/face_refs_audit.py`, tests in `tests/unit/test_face_refs.py`:
  sort, undo, quarantine and back, Explorer rename, copy on another drive, edited photo,
  identical copies tie broken by name).
- Relocation after `import` and the home page's audit: `relocate_after_audit` ends
  `AuditService.run`, which `mh audit`, `import` (`import_run`, `import_copies`) and the home
  page (`cli/home_audit`) all call. New end-to-end proof: `tests/integration/test_face_rename_audit.py`
  (a folder renamed outside, a real audit, the face's path rewritten, its id kept).
- The places page's take-back sends `id` (`places/board.py` → `take_back(config_file, act.id)`),
  kept as decided 2026-11-02.

No follow-up filed; no new limit.
