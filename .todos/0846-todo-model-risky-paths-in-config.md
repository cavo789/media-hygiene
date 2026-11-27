# todo_model.py: risky paths in a config file, several IDs per call

- **Priority**: Low
- **Batch**: claude-tooling
- **Depends**: —
- **Files**: `.claude/scripts/todo_model.py`, `.config/todo_model_risky_paths.txt`, `.claude/commands/todo/iterate.md`

## Context

`RISKY_PATHS` (line ~30) is a tuple of project paths inside a script shared with the maintainer's
other repositories, matched with `startswith`.

## Change

- Move them to `.config/todo_model_risky_paths.txt` (one glob per line, `#` comments), matched with
  `fnmatch` against the path and its file name, merged with generic defaults: `Dockerfile*`,
  `*compose*.y*ml`, `.devcontainer/*`, `install*.sh`, `.env*`, `*migrations/*`, `*.sql`.
- Accept several IDs: `todo_model.py 0448 0450` prints one line each, `<id> <model>: <reason>`.
  `/todo:iterate` picks a lot's model in one call (opus unless every member is sonnet).
- Keep the rule order and the existing tests green; add one for the file + defaults and one for
  several IDs.
