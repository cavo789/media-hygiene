# 0849 — A missing linked people file loads empty with a warning; config tidy offers to unlink it

- **Priority**: Medium
- **Batch**: backlog
- **Depends**: none
- **Files**: `src/media_hygiene/config/loader.py` (`linked_layer`), `src/media_hygiene/config/face_refs.py`, the `config tidy` kinds (0812, commit e4750156)

## Why (review of feedback-2026-11-27-iterate, maintainer's choice)

Today a person linked from `config.toml` whose `/config/people/<name>.toml` is gone makes the settings fail to load, so no command runs and `config tidy` cannot report it.

## Do

- A missing linked file loads as an empty list; one warning names the file and the person (CLI one-liner, and on the pages that load settings).
- `config tidy` lists it as a kind, ticked by default; `--apply` unlinks it (backup, read back), like the town renames of 0812.
- Tests: file removed, file renamed in Explorer (another name), file back again (warning gone).
