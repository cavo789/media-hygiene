# 0280 — One browser tab for the home page and its steps, not a new one each time

- **Priority**: high
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/cli/templates/mh.ps1.j2, src/media_hygiene/cli/templates/mh_menu.ps1.j2, src/media_hygiene/cli/templates/mh.sh.j2, src/media_hygiene/review/templates/home_run.js.j2, src/media_hygiene/services/launcher.py, tests/unit/ (launcher templates), tests/measure/mh-measure.ps1
- **Needs maintainer**: a check on the Windows PC (desktop shortcut, a few steps run from the home page)

## Context

The maintainer ran a few actions from the home page (2026-10-20, after 0277 made it fast).
Each time the step ran in PowerShell, then a **new browser tab** opened: after a while two
"Media Hygiene — Accueil" tabs and two "Tri des rafales" tabs, all on `127.0.0.1:8088`.
The expected flow is one tab that the page itself brings back.

## Cause (from reading the code, not verified on Windows)

- `_mh_home` (`mh_menu.ps1.j2`) loops: `mh home` → step → `mh home` again. Each `mh home`
  (and each page step, e.g. `review`) goes through `mh.ps1.j2`'s `if ($page)` block, whose
  `Start-Job` opens the URL with `Start-Process` as soon as it answers (0178): **one new tab
  per loop turn**.
- Meanwhile the old tab already comes back by itself: `waitForComeBack()` (`home_run.js.j2`)
  polls `/api/state` and reloads once the server is gone then back. So the old tab and the new
  one both show the home page.
- A page step (`review`, "Tri des rafales") opens its own tab the same way; its "Home" link
  then leaves that tab on the home page while the first home tab reloads too.

## Expected

1. Open the browser only for the **first** page of an `mh` call: the loop of `_mh_home`
   tells `mh` not to open it again for its next `mh home` (e.g. a `$global:` flag or an
   argument read by the `if ($page)` block), since the existing tab reloads itself.
2. Decide for page steps (`review`, `review-sort`, `places`, `browse`): navigate the home tab
   to the step's page and back (the page waits on the same port), instead of a new tab, or
   keep a new tab but never a second home tab. Say which in the docs of both languages.
3. Same in `mh.sh.j2` (WSL) if it opens the browser.
4. Tests on the rendered scripts; a `mh-measure.ps1` step (or 14h updated): home, 3 steps
   (console, page, form), count the tabs; captures to rerun if a page text changes.

## Decided (2026-10-21)

By the maintainer, in the chat: one tab from start to end. A page step started from the home
page shows in the home page's own tab; its "⌂ Back to the home page" brings that tab back to
the space it was left from (`#clean`…). Every page opened from the home page shows that link.

## Status — PARTIAL (2026-10-21)

### Done
- Cause confirmed in the code, a second one found: (1) each page of the `_mh_home` loop opened
  a new tab (Start-Job / `_mh_browse`); (2) the waiting home tab polled `/api/state`, which
  `review` answers too, so it reloaded into the review page, the URL still `/#clean`: two tabs
  on review, closing one kept the page alive (0262 presence), only Ctrl+C got out; (3) the
  relay (`MEDIA_HYGIENE_LAUNCHER_STEPS`) went to `home` and `browse` only, so `review`,
  `places`… never showed "⌂ Back to the home page".
- `mh.ps1.j2` / `mh_menu.ps1.j2`: `$global:MediaHygieneTab`, set by the loop once its first
  page answered; the `if ($page)` block opens the browser only without it. `mh.sh.j2`: the same
  with a `local _mh_tab` of `_mh_home`.
- `launcher.py`: the relay goes to every page command (`home`, `browse` and `pages`).
- `home_run.js.j2`: the section (`location.hash`) kept in `sessionStorage` (`mh-home-section`)
  at each step; the tab waits on `/` (any page answers it), then `location.replace("/")` for a
  page step, `reload()` for a console step. `home_link.html.j2` and `browse_apply.js.j2` come
  back to `"/" + section`.
- The run dialog says it (en + fr): *{command} opens its page here, in this tab; its ⌂ Back to
  the home page brings you back to this very place.* `commands/home.md` (en + fr) updated.
- Tests: `test_launcher_home.py` counts the tabs mh opens (bash, real run of the rendered
  script): home → review → home → history → home opens **1** tab (4 without the fix,
  checked); `mh review` alone opens its own, unrelayed; PowerShell text asserted.
  `test_home_given.py` (dialog, section kept, wait on `/`), `test_page_headers.py` (every page
  returns to the section). Unit suite 2,466 passed; commit gate clean.
- `mh-measure.ps1` step 14h: review in the same tab, back to the Clean space, tabs counted.

### Not done
- The check on Windows (PowerShell 5.1, the maintainer's browser): `.\mh-measure.ps1 -Only 14
  -Count 1` with an image built from this commit, part 14h.
  **Reason:** needs Windows, Docker Desktop and a real browser.
- Closing the page's tab still ends the page and `mh` with it, the prompt back (0262), instead
  of opening the home page again as proposed in the chat: with one tab, closing it means
  leaving. To confirm by the maintainer.
- `docs_screenshots`: the run dialog text changed (home captures, if one shows it).

## Closed (2026-10-21)

Checked by the maintainer on Windows (`mh-measure.ps1 -Only 14`, measures-20261021-0800): the
review page in the same tab, *Back to the home page* back on the Clean space, **1 tab** on
127.0.0.1 at the end, Ctrl+C clean. Closing the tab ends the page and `mh` (0262) — kept, by
the maintainer. The console step easy to miss (the browser stays in front) is TODO 0285.
