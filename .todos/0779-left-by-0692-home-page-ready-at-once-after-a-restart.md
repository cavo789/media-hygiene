# 0779 — What 0692 left: Home page ready at once after a restart, whatever the tool folders hold

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0692-home-page-ready-at-once-after-a-restart.md`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/cli/home_state.py`, `src/media_hygiene/cli/status_safety.py`, `src/media_hygiene/services/safety.py`, `src/media_hygiene/services/only_copies.py`, `src/media_hygiene/review/home_app.py`
- **Needs maintainer**: a second start of `mh` on Windows + Docker Desktop

Split from section 0692 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0692-home-page-ready-at-once-after-a-restart.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Second start of `mh` (container removed, nothing changed): the home page is drawn
- The safety card shows the same facts as before (equivalence test), and follows each
- No traceback, no endless spinner if the card's route fails (message in the card)
- New strings through `_()` + French; both documentation languages if a capture changes

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
- Part of this needs the maintainer (see *Needs maintainer*): do the code part, leave the rest said in the report, never guess it.
