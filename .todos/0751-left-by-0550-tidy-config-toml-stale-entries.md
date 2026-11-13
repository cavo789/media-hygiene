# 0751 — What 0550 left: Tidy config.toml: remove the entries that point at nothing any more

- **Priority**: Medium
- **Batch**: backlog
- **Depends**: —
- **Files**: `.todos/DONE/0550-tidy-config-toml-stale-entries.md`

Split from section 0550 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0550-tidy-config-toml-stale-entries.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The web page with ticks (memory: visible in web or nonexistent).
- `[[classify.place_photos]]` line by line, town renames vs GeoNames, `people` files.
- A `path` rule aimed at a root the index never covered still looks stale when the index
- Every kind of the table detected, with tests (folder renamed, moved by `sort`, drive
- Nothing removed without being shown and ticked; backup copy; result read back
- Comments and order of `config.toml` kept (test on the default template)

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Decided (2026-11-13)

A `path` rule aimed at a root the index never covered is left alone by tidy: never shown as stale, never removed (choice by the maintainer, review of `.claude/plans/feedback-2026-11-13-iterate.md`).
