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

## Status — PARTIAL (2026-11-13)

### Done
- Checked: the chip, the tab title and the end toast are on every page extending
  `page_frame.html.j2` (`step_chip.html.j2` included by the frame, the home page, the album
  page), and the end says *Done: <stage>.* / *Stopped (code n): <stage>.*: only unticked here.
- The step's 👉 *What next* line now follows that end: `print_advice` writes it, plain, to
  `.mh-step-next.json` when the step runs beside the home server (`services/step_next.py`),
  `GET /api/step` carries it as `next` once done, the chip, the home page's dialog and *Apply
  now* add it after their end sentence; a new step forgets it first. Tests
  `tests/unit/test_step_next.py`. Docs EN+FR `commands/home.md`.

### Not done
- The step's summary first line in the end message.
  **Reason:** no single place prints a step's summary (each command draws its own table); the 👉
  line is the one shared sentence. A follow-up would need each summary to name its first line.
- Browser check of the toast with the 👉 line: CI's headless Chromium, not run here.
