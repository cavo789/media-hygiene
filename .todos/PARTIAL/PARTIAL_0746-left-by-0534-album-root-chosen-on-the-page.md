# 0746 — What 0534 left: Albums folder chosen on the albums page

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: —
- **Files**: `.todos/DONE/0534-album-root-chosen-on-the-page.md`, `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/places/toml_edit.py`

Split from section 0534 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0534-album-root-chosen-on-the-page.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The decided move: album link folders recreated in the new folder, the old one emptied of its
- A tree folder chooser (the field is a typed path). **Reason:** the search tree lists the

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- The decided move (album link folders recreated in the new folder, the old one emptied of its
  links): already done by 0582 (`.todos/DONE/DONE_0582-album-link-folders-follow-a-changed-root.md`).

### Not done
- A tree folder chooser for the albums folder (the field stays a typed path).
  **Reason:** the search tree lists only the library's folders, and an albums folder is often a
  new one: it needs a chooser over the mounted drives that can also name a new folder — a design
  of its own (which mounts to list, how deep, a phone never), not reached in this run.
