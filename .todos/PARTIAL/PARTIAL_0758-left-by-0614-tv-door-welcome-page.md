# 0758 — What 0614 left: The TV's address `http://<PC>:8089/` opens a welcome page, not the phone's steps

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0614-tv-door-welcome-page.md`, `src/media_hygiene/services/slideshow_here.py`, `src/media_hygiene/slideshow/tv_door.py`

Split from section 0614 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0614-tv-door-welcome-page.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The line of index facts (photos, years covered).
- The *On this day* background.

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- The line of index facts under the title: « 12,345 photos and videos, from 2004 to 2026 »
  (`slideshow/tv_facts.py`: one read-only query of the index, broken files left out; no
  index or an unreadable one: no line), in both servers (`TvDoor.index_file`,
  `slideshow_here`). Tests: `tests/unit/test_tv_facts.py`; docs en + fr
  (`commands/slideshow.md`); French strings.

### Not done
- The *On this day* background.
  **Reason:** waits for *On this day* itself (PARTIAL 0461: no month-day query over the index
  yet); nothing to show until then.
- `docs_screenshots` to run (the welcome page gained a line); tracked with the captures (0717).
