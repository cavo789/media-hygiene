# 0739 — What 0498 left: The HTML reports in the home page's look

- **Priority**: Low
- **Batch**: page-shell
- **Depends**: —
- **Files**: `.todos/DONE/0498-reports-in-home-look.md`, `src/media_hygiene/report/templates/base.html.j2`

Split from section 0498 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0498-reports-in-home-look.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The reports opened inside the home page's own frame (server-rendered with `shell*.j2` and the current-space highlight): the report files are static and served as-is by `review/report_files.py`; the http reveal is a client-side stand-in.

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
