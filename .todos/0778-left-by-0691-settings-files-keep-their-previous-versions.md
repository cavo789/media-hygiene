# 0778 — What 0691 left: Settings, people, events and albums files keep their previous versions: a page's save can be undone

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `.todos/DONE/0691-settings-files-keep-their-previous-versions.md`, `src/media_hygiene/review/config_saving.py`, `src/media_hygiene/text_files.py`, `src/media_hygiene/share/album_store.py`, `src/media_hygiene/services/page_undo.py`, `src/media_hygiene/review/templates/undo_toast.html.j2`

Split from section 0691 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0691-settings-files-keep-their-previous-versions.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The Undo toast after a settings save, Ctrl+Z, and the *Versions* page (date, short diff of
- `classify/remember_rule.py` rolls `config.toml` back with `write_bytes(before)` after a
- Index-only data (hand-typed tags, landmarks): covered by `mh backup` and the tag pages' own
- Every save path of the pages goes through the helper (a test lists the writers of
- Save → Undo → the file is byte-identical to before (test per file kind)
- The history never grows past its bound; restored and moved folders handled (tested)
- Docs EN + FR

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
