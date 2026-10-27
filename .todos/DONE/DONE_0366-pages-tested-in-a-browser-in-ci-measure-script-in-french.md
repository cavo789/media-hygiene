# 0366 — The pages tested in a real browser in the CI (Playwright in Docker); `mh-measure.ps1` in French

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0355, 0356
- **Files**: `tests/e2e/test_pages_browser.py`, `tests/support/docs/screenshots.py`, `tests/support/docs/browser.py`, `tests/support/pages_browser.py`, `tests/e2e/conftest.py`, `.github/workflows/ci.yml`, `tests/measure/mh-measure.ps1`

## Context

Asked by the maintainer (2026-10-25). Step 35 of `mh-measure.ps1` timed the pages by two Enters:
right for 8 s (*measured* 7.6–8.7 s, 0354), meaningless now that search shows at once (0356) —
the reaction is longer than the wait. Its question 35e was not understood, step 36 neither: the
script is in English. The maintainer has no Playwright on the PC: it must run from a Docker
image.

The project already runs Playwright in Docker for the documentation's screenshots
(`tests/support/docs/screenshots.py`: `mcr.microsoft.com/playwright/python:v1.57.0-jammy` plus
the Python package, image `media-hygiene-docs-browser`; `browser.py` drives the pages served on
`127.0.0.1:8088`). The same image can test the pages.

What a browser test can and cannot prove: it runs on Linux with `mh.sh`, in the CI; it proves
the pages, the tab following the servers and the timings measured by the browser itself; it
does not prove `mh.ps1`, Windows or Docker Desktop (those stay a short check by hand, below).

## What to do

1. **A browser test in the e2e suite** (`pytest -m e2e`, run by the CI on every pull request,
   image *Image end-to-end tests*): the image of the branch serves `mh` alone through `mh.sh`
   with a test library (the demo tree), the Playwright image drives Chromium:
   - home → *search*: the search page shown, its first search answered; home ← *Back to the
     home page*: the home page shown — each under a bound, timed by the browser
     (`performance.getEntriesByType("navigation")`, the time to the first answer of
     `/api/search`), the figures written to the test's log (*measured*, CI runner);
   - a console step (`history`): the home page stays open (no *This page is closed*), the
     dialog says *runs in the window of mh*, then *done*; the page refreshed in place;
   - back on the home page after a page that is not served by it yet (a review): the tab follows
     the next server without F5 (the bug of 0354), ten times in a row;
   - no container started by a click on search/browse (Docker's events over the test).
   Reuse the image and the helpers of `tests/support/docs/` (move the shared part to
   `tests/support/pages_browser.py`); the Playwright image runs Python 3.10: nothing newer in
   the code it runs.
2. **`mh-measure.ps1`**: step 35d (the two Enters) and 35e removed — replaced by item 1; 35a–35c
   kept (the container and the phases of search on the maintainer's index, which only the PC
   has). Step 36 becomes three yes/no questions by hand (home opens; a console step runs in the
   window while the page stays open; Quit then `mh` again).
3. **`mh-measure.ps1` in French**: every question and line shown to the maintainer in French.
   The script stays ASCII only (an accented byte breaks Windows PowerShell 5.1's console code
   page, TODO 0098): French without accents, or the accented letters written with `[char]`
   (e.g. `"r$([char]0x00E9)sultat"`); the results file stays in English (Claude reads it). A
   test checks the script is ASCII (`LC_ALL=C grep -P '[^\x00-\x7F]'` finds nothing).

## Acceptance

- The CI's e2e job runs the browser test on every pull request and fails on a page that does not
  come back by itself, or on a click that starts a container.
- `mh-measure.ps1` asks its questions in French, no step asks to time a page by hand.

## Gain

Page regressions caught by the CI, without the maintainer (today: found by hand on Windows, the
F5 bug once in three returns, *measured* 35d); real timings instead of two Enters; a measure
script the maintainer understands.

## Status — PARTIAL (2026-10-27)

### Done
- `tests/e2e/test_pages_browser.py`: `mh` alone through `mh.sh` (reports on a host folder so
  the step files exist, demo audited first), Chromium in the Playwright image on the host's
  network runs `tests/support/pages_walk.py`: search (click → page → first `/api/search`
  answer, navigation timing) and browse, each back by *⌂ Back to the home page*, under 10 s;
  no container of the image started meanwhile (`docker events`); `history` as a console step:
  the dialog names it, the page never reloads nor closes, `/api/step` says done, code 0; a
  review (its own server) then back ten times, the tab following without F5. Figures printed
  to the CI log. Runs only with `MEDIA_HYGIENE_E2E_BROWSER=1` (set in `ci.yml`'s e2e job) and
  `MEDIA_HYGIENE_E2E_HOST_DIR`: never on the maintainer's PC by default.
- Shared part moved to `tests/support/pages_browser.py` (image, `BrowserRun`, `run_browser`);
  `docs/screenshots.py` uses it.
- `mh-measure.ps1`: 35d/35e and `ClickTimed` removed; step 36 = three yes/no questions in
  French (results logged in English); `tests/unit/test_measure_script.py` checks ASCII only.

### Not done
- The browser test was **not run locally** (needs the image built + CI's host folder): its
  first run is the CI of the pull request; selectors (`#runDlg`, `#homeLink`, `onRun`,
  `BY_ID`) read from the templates, may need a fix there.
- The rest of `mh-measure.ps1` (steps 1–35, ~230 questions and lines) still in English.
  **Reason:** scope; mechanical, a TODO of its own (keep ASCII, `[char]` for accents).

## Inbox (2026-10-27)

- The rest of `mh-measure.ps1` in French → 0422. The browser test's first run is the CI's. Closed to DONE (maintainer, 2026-10-27).
