# 0742 — What 0513 left: One interface: every action of mh run from its page, PowerShell only to start it

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: —
- **Files**: `.todos/DONE/0513-one-interface-every-action-from-the-page.md`, `src/media_hygiene/cli/menu_entry.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/services/home_pages.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `tests/unit/test_menu_catalog.py`, `documentation/en/commands/home.md`

Split from section 0513 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0513-one-interface-every-action-from-the-page.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The 32 steps. **Reason:** an umbrella; the work is 0586 (writing steps, needs a Windows run), 0506
- The chapter saying "everything from here": it would be false before that.

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — UNNEEDED (2026-11-13)

Redundant: an umbrella. The steps still leaving the page are counted by
`test_the_steps_leaving_the_page_only_shrink` (`tests/unit/test_menu_catalog.py`) and the work is
in open TODOs: 0586 (writing steps from the page, needs a Windows run), 0506 (host steps), 0512
(typed pages); 0594 is done. The "everything from here" chapter is written when that list is empty.
