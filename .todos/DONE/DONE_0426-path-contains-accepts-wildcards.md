# 0426 — Search: "Path contains" accepts wildcards and regex

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/search/statements.py, src/media_hygiene/services/search.py, src/media_hygiene/search/templates/search.html.j2, documentation/en/commands/search.md, documentation/fr/commands/search.md

## Context

Reported by the maintainer (2026-10-27): on the search page, "Path contains" (FR "Le chemin
contient") set to `*mov` finds nothing, while the collection holds 279 `.mov` videos (count
given by the maintainer, not measured here). Cause found by reading the code:
`search/statements.py:72` filters with `instr(fold(files.path), ?) > 0`, a plain substring
match, so the `*` is searched literally. `mov` or `.mov` alone would match (and also match
`movies/` folders), which a user cannot guess.

## Acceptance

- [ ] `*` (any characters) and `?` (one character) are wildcards in "Path contains"; `*mov`
      and `*.mov` find every `.mov` file, case-insensitive (`.MOV` too).
- [ ] Without a wildcard, the current substring behaviour is unchanged.
- [ ] SQL `LIKE` special characters typed by the user (`%`, `_`) stay literal (escaped).
- [ ] Regex on an explicit marker only, so ordinary paths never turn into patterns: a value
      written `/…/` (e.g. `/\.(mov|mp4)$/`) is a Python regex, case-insensitive, run by a
      `REGEXP` function registered on the SQLite connection (`create_function`,
      `deterministic=True`). Without the slashes, `Vacances (2019)` or `a+b` stay literal.
- [ ] An invalid regex shows a one-line message under the field (translated), never an empty
      result or a traceback.
- [ ] Measure the regex cost on the demo index and on a synthetic 100 000-row index (Python
      call per row vs `instr`); say *measured* in the close-out.
- [ ] `mh search --folder` (cli/cmd_search.py) takes the same syntax.
- [ ] The field's hint/placeholder and the search page docs (EN + FR) say wildcards work.
- [ ] Unit tests: `*mov`, `*.mov`, `.MOV`, plain substring, `%`/`_` literal, `/\.(mov|mp4)$/`,
      invalid regex, `Vacances (2019)` literal.
