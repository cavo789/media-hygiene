# 0262 — The other pages stop once no tab shows them, without reopening home

- **Priority**: Low
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/review/ending.py`, `src/media_hygiene/review/presence.py`, `src/media_hygiene/review/templates/home_link.html.j2`, `src/media_hygiene/services/review_serving.py`, `src/media_hygiene/services/reviewing.py`, `src/media_hygiene/services/sort_reviewing.py`, `src/media_hygiene/services/places.py`, `src/media_hygiene/services/people_page.py`, `src/media_hygiene/services/search_pages.py`, `src/media_hygiene/services/phone_review.py`, `src/media_hygiene/constants.py`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`

Follows 0261 (home page: a Quit button, and it stops once no tab shows it), whose item 3
was left for this TODO: the other pages need more than the home page did.

## Today

- `review` (and `--near`, `--pairs`, `--junk`, `--gone`), `review-sort`, `places`, `people`,
  `search`, `phone --free`: their server ends on Ctrl+C or `POST /api/stop` (the "⌂ Home" link),
  and most callers **ignore the code** `run_server` returns (`asyncio.run(run_server(...))`):
  the command exits 0 either way.
- In the loop of `mh` alone (`_mh_home`, PowerShell and bash), a step that ends with 0 or any
  code ≤ 100 opens the home page again.

## To do

1. Every page tells its presence (`review/presence.py`, the same `POST /api/alive`), through
   the shared `home_link.html.j2` script, so each template gets it in one place.
2. A tab closed must **not** reopen home in a new tab (what exit code 0 does in the loop): a
   distinct exit code, e.g. `ExitCode.PAGE_CLOSED` (a free value, not 0/1/2/130 nor ≥ 100),
   returned by each command when its presence closed it — so each caller must return the
   code of `run_server`/`serve_until_ended` instead of dropping it.
3. The loops of `mh.ps1` (`mh_menu.ps1.j2`) and `mh.sh` (`mh.sh.j2`, 198/200 lines: plan the
   split first) end on that code, prompt back, exit code 0 for the user; the window title and
   the sound of long commands treat it as a success.
4. One console line per page, as for home ("The page's tab was closed: …").
5. Tests: per page, a leaving tab ends it with the new code; the rendered loops end on it
   (both scripts); "⌂ Home" still reopens home (0). Docs en + fr where each page says
   "Ctrl+C stops it".

## Gain

Estimated: the same as 0261 for every page: closing the tab, the gesture users make, frees the
port and gives the prompt back, instead of a page left running until Ctrl+C.
