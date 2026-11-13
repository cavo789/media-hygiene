# 0755 — What 0585 left: Intruder files page: no way back home, and a sidebar of shortcuts that looks clickable but is not

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `.todos/DONE/0585-intruders-page-home-link-and-dead-sidebar.md`

Split from section 0585 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0585-intruders-page-home-link-and-dead-sidebar.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- *Back to the home page* on the page opened by a typed command (first acceptance line).
- The intruders page has *Back to the home page*, typed or opened from home
- No sidebar item looks clickable without being one, on any page (test)

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — UNNEEDED (2026-11-13)

Redundant: checked against the code.
- *No sidebar item looks clickable without being one, on any page*: already tested over every page
  of `SHELL_PAGES`, typed and from home (`tests/unit/test_page_headers.py`,
  `test_typed_in_the_console_no_shell_entry_looks_clickable`,
  `test_opened_from_home_every_shell_entry_is_a_link_and_the_way_back_is_there`).
- *The intruders page has Back to the home page*: opened from home, done and tested (same test).
- Typed by a command: the very work of 0512 (`Needs maintainer`: the launcher's exit code, a run on
  Windows PowerShell 5.1 + Docker Desktop). Closes with 0512, nothing to do here.
