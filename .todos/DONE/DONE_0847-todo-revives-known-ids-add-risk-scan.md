# 0847 — TODO workflow: Revives, todo_known_ids.sh, /todo:add risk scan

- **Priority**: Low
- **Batch**: claude-tooling
- **Depends**: —
- **Files**: `.claude/skills/todo-authoring/SKILL.md`, `.claude/commands/todo/run.md`, `.claude/commands/todo/plan.md`, `.claude/commands/todo/inbox.md`, `.claude/commands/todo/add.md`, `.claude/scripts/todo_known_ids.sh`, `.claude/scripts/todo_plan_tables.sh`

## 1. Revives — a finished remainder closes its PARTIAL

- todo-authoring: optional header bullet `- **Revives**: <NNNN>` on a TODO filed for the remainder
  of a `PARTIAL_NNNN` (or `BLOCKED_`) file.
- `/todo:run` close-out: when that TODO ends DONE, append `## Status — DONE (<date>)` ("remainder
  completed by <ID>") to the revived file and move it to `DONE/`.
- `/todo:plan`'s *Partially done* table: a "Revived by" column.
- `/todo:inbox`, "an answer that asks for work": files the new TODO with `Revives`.

## 2. Anti-duplication by script

`.claude/scripts/todo_known_ids.sh [todos-dir] [--open]` prints `ID<TAB>STATUS<TAB>title` for
every TODO in `.todos/` and its status subfolders (hidden folders pruned, like
`todo_next_id.sh`), sorted by ID; `--open`: the flat backlog only. The todo-authoring
anti-duplication step and `/todo:add` read it instead of listing files by hand.

## 3. /todo:add — a quick risk scan

Before writing, scan the task for hidden load-bearing assumptions and ask *one* question only for
the line that applies (most tasks: none): a resource several people/systems use (shared vs single
owner), an environment-specific value (URL, path, credential) confirmed only where the conversation
runs, an external dependency that may be unreachable elsewhere. Fold the answer into Context. End by
reminding the user to run `/todo:plan` (never run it).
