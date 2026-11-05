# 0513 — One interface: every action of mh run from its page, PowerShell only to start it

- **Priority**: High
- **Batch**: one-interface
- **Depends**: 0503, 0505, 0506, 0512, 0514 (this TODO is the umbrella; it closes when its goal below is met)
- **Files**: `src/media_hygiene/cli/menu_entry.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/services/home_pages.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `tests/unit/test_menu_catalog.py`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Asked (maintainer, 2026-10-30)

"Do we have a TODO to converge towards a single interface: everything I launch stays in the
mh web page, no more back-and-forth to PowerShell? It is the case for most read-only pages;
could we tend to it for everything?" Thinking and TODOs only, no code.

## Where we are (catalog counted, 2026-10-30)

Measured by parsing `cli/menu_catalog_*.py` (`Step(...)`, its `Kind`): **52 actions**.

| Kind | Count | Today from the home page | Leaves the page? |
|---|---|---|---|
| `PAGE` | 13 (`review*`, `search`, `people`, `places`, `slideshow*`, `shrink`, `home`) | home ends, the page's container starts on the same port, home comes back after | no typing, but a restart each way (0503's port race: page lost, seen today) |
| `CONSOLE` | 26 (`audit`, `clean`, `import`, `classify`, `sort`, `undo`, `apply`, `backup`, `config`…) | "switch to your PowerShell window" (`T.runsConsole`) | **yes** |
| `HOST` | 13 (`folders-add/remove`, `nas-add`, `phone`, `update`, `open`, `explorer`, `push`…) | the server ends, `mh.ps1` runs it on Windows, then home again | yes (prompts in the console) |

So about half the actions (26 + 13 = 39 of 52, 75 %) still send the user to PowerShell or
restart the page. Not "most read-only pages are fine" by accident: they are `PAGE` kinds.

## What blocks, by cause (each a separate TODO)

1. **Page switches restart a container** → 0503 (wait for the port), then: can the home
   server serve each `PAGE` itself (as `search`/albums already are, `header.shared`, 0356)?
   0491–0498 put pages in the home *frame*; this asks them in the home *server*: no restart,
   no port race, Back home is a plain link. New TODO to file when 0494 lands: per page, what
   it needs that the home server lacks (its own session state, a mount, an option).
2. **Short console steps** (`config`, `backup`, `history`, `reports-prune`…) → 0505 (output
   in a dialog).
3. **Long console steps** (`audit`, `clean`, `import`, `classify`, `sort`, `undo`, `purge`,
   `apply`) → **0514**: a progress view in the page (the Rich progress sent as events, Stop button,
   summary and 👉 line, questions asked in the page first).
4. **Host steps** → 0506 (beside the page). Some must change the container's mounts
   (`folders-add/remove`, `nas-add`, `phone`) or its image (`update`): a restart cannot be
   avoided, but `mh` can do it **unasked by the user** while the page shows "mh restarts…"
   and comes back — no typing. To check in 0506; file a follow-up if 0506 keeps a console
   prompt for them.
5. **Pages opened by a typed command** → 0512 (Back home and Apply there too).
6. **Redundant steps** that only make sense in a console → 0504 (hidden on the page).

## What stays in PowerShell (on purpose)

- Starting `mh` (or a shortcut / the right-click entry, which type it for the user).
- Docker Desktop stopped: the page cannot exist; `mh` starts it (already, 0174).
- A fatal error of `mh.ps1` itself.

## Goal and how it is checked

- A test over the catalog: every step shown on the page runs without "switch to the
  window" (no `T.runsConsole` path) — counted, with the remaining ones listed in this TODO
  until the list is empty. Start: 39 of 52 (measured above).
- Docs EN + FR: the home page chapter says "everything from here"; the console stays
  documented as the power user's way. `docs_screenshots` after each child TODO.

## Questions for the maintainer

- A long step (an audit of hours) run from the page: if the browser tab is closed, does it
  go on (proposed: yes, the page shows it again when reopened) or stop?
- The console stays a full interface (scripts, power users): proposed yes, never removed.

## Where the user gains

Before: 39 of 52 actions (75 %) leave the page or restart it. After: 0 to type; the console
only to start mh.

## Decided (2026-11-03, iterate)

By the maintainer: a long step started from the page goes on when the tab is closed (the page shows it again when reopened); the console stays a full interface, never removed.

## Status — PARTIAL (2026-11-05)

### Done
- The counting test: `test_the_steps_leaving_the_page_only_shrink` (`tests/unit/test_menu_catalog.py`,
  `STILL_IN_THE_WINDOW`): 32 of the 49 steps the page shows still leave it (measured from the catalog;
  21 console, 11 host). Was 39 of 52 by the older count, which included `PAGE`'s restarts and `web=False`.
- Docs EN + FR (`commands/home.md`): the goal, what remains, the console stays a full interface.
- Cause 1 filed (0494 landed): 0594.

### Not done
- The 32 steps. **Reason:** an umbrella; the work is 0586 (writing steps, needs a Windows run), 0506
  (host steps), 0512 (typed pages), 0594 (page steps), remainder of 0505. Close when the list is empty.
- The chapter saying "everything from here": it would be false before that.
