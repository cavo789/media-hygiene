# 0762 — What 0661 left: A running step is shown on every page: chip in the header, tab title, notification

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: —
- **Files**: `.todos/DONE/0661-running-step-shown-on-every-page.md`, `src/media_hygiene/review/templates/page_header.html.j2`, `src/media_hygiene/review/templates/shell_top.html.j2`, `src/media_hygiene/review/templates/home_notify.js.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/step_watch.py`, `documentation/en/commands/home.md`

Split from section 0661 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0661-running-step-shown-on-every-page.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The end message is *Done: <stage>.* / *Stopped (code n): <stage>.*: `/api/step` does not carry
- The chip, the title and the end toast on every page extending `page_frame.html.j2`

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
