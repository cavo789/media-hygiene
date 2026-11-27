# 0824 — Albums folder chosen in a folders tree, not typed

- **Priority**: Low
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/search/` (the folders tree), `src/media_hygiene/places/toml_edit.py`

Decided by the maintainer in the inbox of 2026-11-14 (follows `.todos/PARTIAL/PARTIAL_0746-*.md`).

## Context

The albums page asks for the albums folder as a typed path: a typo saves a folder that does
not exist. The library already has a folders tree (`search/`).

## Proposal

Reuse that tree as a chooser in a dialog (rule: reuse the shared component, add to it what
is missing, never a page-local copy); the choice saved as today (`toml_edit`, read back from
disk and shown). The typed field stays as the fast path.

## Acceptance

- [ ] The folder picked in the tree is saved, read back and shown
- [ ] The library's tree unchanged (its tests); one component for both
- [ ] French strings; docs EN + FR of `album`; `docs_screenshots` said

## Status — DONE (2026-11-27)

*📂 Pick in my folders…* on the albums page opens the library's folders tree in a dialog (`review/templates/folder_chooser.html.j2`, `window.mhPickFolder`; the tree files moved to the shared templates, the library includes the same ones); `GET /api/album-root/folders` (`search/album_root_tree.py`, from the index file); a click saves through the existing form (`toml_edit`, read back and shown). The typed field and the 0797 drive list stay. Tests: `test_album_root_desk.py`, `test_album_folder_chooser.py`. `docs_screenshots` should run (albums page).
