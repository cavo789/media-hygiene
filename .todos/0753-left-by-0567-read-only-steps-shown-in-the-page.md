# 0753 — What 0567 left: Home page: status, folders, reports, inventory, config shown in the page

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `.todos/DONE/0567-read-only-steps-shown-in-the-page.md`, `src/media_hygiene/services/home.py`, `src/media_hygiene/services/home_pages.py`, `src/media_hygiene/services/status.py`, `src/media_hygiene/services/history_here.py`, `src/media_hygiene/review/templates/home.html.j2`

Split from section 0567 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0567-read-only-steps-shown-in-the-page.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- `folders`: a host step (`Kind.HOST`, run by `mh.ps1` on Windows), the container cannot list it.
- The text is shown preformatted (Rich's plain export), not as a styled panel/table.

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
