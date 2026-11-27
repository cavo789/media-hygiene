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
