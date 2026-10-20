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
