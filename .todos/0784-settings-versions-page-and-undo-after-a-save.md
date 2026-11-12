# 0784 — Settings: a *Versions* page, and Undo (toast, Ctrl+Z) after a page's save

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/file_history.py`, `src/media_hygiene/review/templates/settings_index.html.j2`, `src/media_hygiene/review/templates/undo_toast.html.j2`, `src/media_hygiene/review/config_saving.py`, `src/media_hygiene/services/page_undo.py`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`

Left by 0778 (from 0691).

## Context

Every save of `config.toml`, `people/<name>.toml`, `events/<year>.toml` and `albums.json` keeps
the file it replaces in `.history/` (`file_history.replace_text`; the 20 newest, 30 days at most),
and `restore_version` puts one back, read back, itself undoable. Nothing on the pages uses it:
`reference-safety.md` tells the user to copy a version over the file by hand. A feature reachable
only by hand counts as missing (*visible in web or nonexistent*).

## Proposal

- A *Versions* page linked from the settings index: per file, its versions (date, a short diff of
  the keys that changed), *Restore this one*; the content read back from the disk and shown.
- The shared Undo toast after a settings save, on every page that saves one (≈ 10 pages, the
  writers listed in `tests/unit/test_file_history.py`): Undo restores the version that save kept;
  Ctrl+Z where the page gives it no other meaning.
- Not a tile page: no wait on PR #80, but the toast goes on pages it touches (people, search):
  those after its merge.

## Acceptance

- [ ] Save → Undo (toast, Ctrl+Z) → the file is byte-identical to before, per file kind
- [ ] *Restore this one* on the Versions page, read back; a version trimmed meanwhile: refused, said
- [ ] Docs EN + FR (`reference-safety.md`: the hand copy replaced by the page); French strings
