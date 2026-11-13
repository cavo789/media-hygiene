# 0756 — What 0588 left: `mh people` from the home page opens in seconds, not 32 s

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0588-people-page-opens-fast.md`

Split from section 0588 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0588-people-page-opens-fast.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- New photos: the page opens at once, their analysis followed in it

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — DONE (2026-11-13)

- The code was already there (0588: the home step opens `/people/` at once, the page analyses the new photos through `/api/people` with its count and Stop); what was missing is the proof in a real browser.
- `tests/e2e/test_people_new_photos_browser.py` + `tests/support/new_photos_walk.py`: the page's own script in Chromium, `/api/people` mocked, EN + FR: the start line at once, "1 of 3", then done (Show visible, Stop hidden) or Stop clicked → stopped; a 403 (off the PC) hides the panel. Measured here: 2 passed in 15.5 s; a mutation (end state `failed`) makes it fail.
- Not done: the timing on Windows (acceptance line 1 of 0588, maintainer's machine); the ~9 s of the cold page outside grouping (0722) is not this TODO: no optimisation made, so no profile needed here.
