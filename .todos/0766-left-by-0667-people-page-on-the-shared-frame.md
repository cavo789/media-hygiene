# 0766 — What 0667 left: People page onto `page_frame`: the stale exception of the frame test removed

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `.todos/DONE/0667-people-page-on-the-shared-frame.md`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/people/templates/people_guide.js.j2`, `tests/unit/test_page_frame.py`

Split from section 0667 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0667-people-page-on-the-shared-frame.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- `mhBusy` on the section buttons (a save is short, the bar's *Saving…* line stays): left for
- `people.html.j2` extends `page_frame.html.j2`; no exception for it in the test

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
