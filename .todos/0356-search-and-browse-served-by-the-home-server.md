# 0356 — `search` and `browse` served by the home server: a click opens them at once

- **Priority**: High
- **Batch**: home
- **Depends**: 0355
- **Files**: `src/media_hygiene/review/home_app.py`, `src/media_hygiene/services/home.py`, `src/media_hygiene/services/search_pages.py`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/folders.py`, `src/media_hygiene/review/shared_routes.py`, `src/media_hygiene/review/local_app.py`, `src/media_hygiene/cli/cmd_search.py`, `src/media_hygiene/cli/cmd_browse.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/search/templates/`, `tests/integration/tags/test_search_command.py`, `tests/integration/tags/test_browse_page.py`, `tests/integration/test_home_page.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`

## Context

Phase 2a of the single server (maintainer, 2026-10-24). Today a click on *search* stops the home
server, starts a container for `search`, and the tab waits for it: 7.6–8.7 s (*measured*,
step 35d, 0354), about 5.5 s after 0354 (*estimated*). `search` and `browse` never change a
photo (`READ_ONLY_COMMANDS`, `cli/safety.py`): the home server, which mounts the photos
read-only, can serve them itself. One server, one index opened once, the names of the people
(1.8 s, *measured*, 35c) and the full-text table (0.4 s) made once per session.

## What to do

1. **The pages under their own prefix.** Several pages reuse the same paths (read in the code,
   2026-10-24): `/` (home, search, review…), `/api/state`, `/api/folders`, `/api/folder`,
   `/api/aside`, `/api/search`. The home server mounts each page's app under a prefix
   (`/search/…`, `/browse/…`), the shared routes once (`/api/alive`, `/api/stop`, `/assets/`,
   `/docs/`, `/person/`); the templates' paths become relative to their prefix (a base path given
   to each page, never a literal `/api/…` in a template — a test greps the templates).
2. **The home page links to them directly** (a plain link, no `/api/step`, no server change): the
   catalog's actions `search` and `browse` say they are served here; *Back to the home page* is a
   plain link too. Multiple tabs work (search in one, browse in another), the browser's Back
   button as well.
3. **Opened by its command** (`mh search`, `mh browse --folder X`): when the home server of this
   `mh` runs (its container label, 0250), `mh` opens the tab on `/search` or `/browse?folder=X`
   at once; else the same server starts with the page as its first one (`/` redirects there).
   `docker run … search` alone keeps working (the same server, the page first). `--port` on a
   running server: one line says the page opens on the server's port. `mh search "words"` (the
   table in the console) is unchanged: no server.
4. **What lived for one page now lives for the session**: the decisions file (`decisions.json`)
   written by two tabs → one lock per file, read again from disk before each write, the write read
   back (the product rule); the open index shared by the pages (one read-only connection per
   page app, never across threads).
5. **Startup of the home page stays fast**: the search index opened at the first request of a
   search page, the names read in a thread at the server's start (`names_soon`, 0354).
6. Presence (0262): the server ends when no tab of any of its pages is alive; Quit ends it all.
7. Tests: both pages through the home server (paths under their prefix, the CLI's options as URL
   parameters), a template without a literal API path, two tabs saving into the decisions file,
   `mh search` with a server running (bash fake docker: no second container, a tab opened).
   The measure step of 0354/0355 timed again: click → page.
8. Docs en + fr: search and browse open from the home page in the same server; their command
   alone still works; screenshots (`docs_screenshots` to run, said, not run).

## Acceptance

- Home → search, search → home, home → browse: each under 1 s on the maintainer's PC (measured,
  step 35 again).
- `mh search`, `mh browse --folder X`, `mh search "plage"` work as before, typed alone.

## Gain

A click on search or browse: 7.6–8.7 s (*measured*) → 0.3–0.5 s (*estimated*: the page and its
first search, 2 ms once the table is built), about −95 %.
