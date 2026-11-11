# 0679 — Developer helper: pages reload by themselves when a template or module changes

- **Priority**: Low
- **Batch**: dev-tools
- **Depends**: —
- **Files**: `.devcontainer/scripts/helpers/tool.sh`, `src/media_hygiene/i18n/templates.py`, `src/media_hygiene/review/respond.py`, `documentation/en/development.md`, `documentation/fr/development.md`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The maintainer asks whether a kind of hot reloading is relevant. For the **user** it
already exists where it matters: the home server sees the settings and the index change
(0358), the language applies live (0644, 0647), a page reloads when a new run answers
(`X-Media-Hygiene-Run`). The shipped image has nothing to reload: its code never changes
while it runs.

For the **developer** (and Claude's sessions) it is missing: after editing a `.j2` or a
module, `hygiene home` must be stopped and started again, then the tab reloaded by hand —
on every iteration of every UX TODO. (To check first: whether the Jinja environment of
`i18n/templates.py` re-reads a changed template; no `auto_reload` is set there, `grep`
2026-11-10.)

## Proposal

- A helper `home_dev` (cheatsheet, `# @cat Tool`): runs the home server from the sources
  with `MEDIA_HYGIENE_DEV_RELOAD=1`: templates re-read when changed; a change under
  `src/media_hygiene/` restarts the process (a small watcher over mtimes — `watchfiles` in
  the `dev` group only if the standard library is not enough; never in the image).
- The restart draws a new `RUN_TAG`: the open tab reloads itself with the existing logic.
- Never read in the shipped image (the variable is ignored without the `dev` group, or the
  code lives in `tests/support/`).

## Acceptance

- [ ] Edit a template → the open page shows it within 2 s, no key pressed
- [ ] `dive_ci` / the image size unchanged; `development.md` EN + FR

## Where the user gains

The developer: about 10–15 s per iteration (stop, start, reload — *estimated*) → about 2 s.

## Status

PARTIAL — `home_dev` is in the cheatsheet (`tool.sh`, exported in `interactive.sh`), documented in
`development.md` EN + FR. Nothing under `src/` changed: Jinja's `auto_reload` is on by default, so a
changed template is served by the next request (*measured*: 9-34 ms from the edit to the new answer,
`curl` loop); a `.py` change under `src/media_hygiene/` restarts the server and `X-Media-Hygiene-Run`
changes (*measured*: 1.1 s from `touch` to the new tag).

### Not done

- An open tab does not reload by itself after a template-only edit (no restart, so no new
  `RUN_TAG`); F5 is still needed. A `.py` edit does reload it.
- `dive_ci` not run (no file of the image changed, so the size is unchanged by construction).
