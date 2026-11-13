# 0757 — What 0601 left: A page runs `mh undo <run>` itself: Undo toast on move to an event and Apply now

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: —
- **Files**: `.todos/DONE/0601-page-undo-route.md`, `src/media_hygiene/review/shared_routes.py`

Split from section 0601 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0601-page-undo-route.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- *Apply now* of the review pages, the people page and the other pages: their servers do not
- *Apply now* in its "applying" mode (the server ends, the home page opens): no toast.

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- Checked: the review pages (bursts, pairs, near, junk, gone, intruders), the people page, the
  person page and library already answer `/api/undo-run` and show the toast (0621): only
  unticked here.
- The phone page (`/phone/`, 0694): its server had a `PageUndo` but the page had neither
  `undo_path` nor the toast. Now it renders both (`services/phone_review.py`,
  `phone_review.html.j2`); test `tests/unit/test_phone_here.py` (route answered under `/phone/`).

### Not done
- *Apply now* in its "applying" mode (the server ends, the home page opens): no toast.
  **Reason:** the page is left; the home page that opens already shows *↶ Undo the last run*
  in its header and the *Still undoable* callout (`home_draw.js.j2`, the `mh undo` step), so the
  run stays one click from undone. A toast there would need the home server to answer
  `/api/undo-run` and the page to know the run id from before; the maintainer decides whether
  that duplicate is worth it. The mode only happens with an `mh` that does not keep the home
  server up (before 0363).
