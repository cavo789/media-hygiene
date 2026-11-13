# 0741 — What 0510 left: Intruders page: the buttons in the sticky bar, one live sentence, folders filtered by the extension ticked, Apply now

- **Priority**: Medium
- **Batch**: intruders
- **Depends**: —
- **Files**: `.todos/DONE/0510-intruders-page-sticky-actions-and-live-sentence.md`, `src/media_hygiene/review/templates/intruders_review.html.j2`, `src/media_hygiene/review/templates/intruders_review.js.j2`, `src/media_hygiene/review/intruders_views.py`, `src/media_hygiene/review/intruders_app.py`, `src/media_hygiene/services/intruders_reviewing.py`, `src/media_hygiene/review/apply_api.py`

Split from section 0510 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0510-intruders-page-sticky-actions-and-live-sentence.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Point 6 (page opened behind): filed as TODO 0577.
- Sentence tests in pytest for the four cases (EN + FR): the logic is JavaScript; checked in

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Resolution (2026-11-13) — DONE

- Point 6 (page opened behind): already closed, `.todos/DONE/DONE_0577-typed-page-opens-behind-other-windows.md`.
- Sentence tests for the four cases (nothing, extensions only, folders only, both; plural and
  singular), EN + FR: `tests/e2e/test_intruders_browser.py` + `tests/support/intruders_walk.py`
  run the page's own script in Chromium (the Playwright image already used by the other page
  walks), `api/state` mocked; the sentence and the button checked. CI only
  (`MEDIA_HYGIENE_E2E_BROWSER=1`); run here once: 2 passed in 3.5 s (measured).
- Nothing user-facing changed: no documentation, no strings.
