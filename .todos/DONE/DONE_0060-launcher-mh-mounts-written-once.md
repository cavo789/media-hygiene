# 0060 — A launcher `mh`: the mounts written once

- **Priority**: High — removes the longest, most error-prone part of every guide
- **Batch**: guidance
- **Depends**: 0059
- **Files**: `src/media_hygiene/cli/` (new `cmd_launcher.py`), `src/media_hygiene/cli/templates/` (new: `mh.ps1.j2`, `mh.sh.j2`), `src/media_hygiene/cli/app.py`, `documentation/en/start/`, `documentation/fr/start/`, `documentation/en/clean/quick-guide.md`, `documentation/fr/clean/quick-guide.md`, `documentation/en/sort/quick-guide.md`, `documentation/fr/sort/quick-guide.md`, `tests/e2e/`

## Context

Filed from the 2026-10-10 usability review. The clean quick guide repeats a `docker run`
of 7–9 lines at every step, nearly identical each time (only `:ro`, `/journal`,
`/quarantine` and `-p` change). Non-readers copy the wrong one, forget `:ro` or a mount.

## Proposal

- `docker run … cavo789/media-hygiene launcher > mh.ps1` (`--shell bash` for WSL) writes
  to **stdout** a script defining a function `mh` with the folders mounted in that run.
  Nothing is written under `/config` (config.toml only).
- `mh <verb> [args]` picks the mounts per verb, with the logic of 0059: `audit`,
  `review`, `inventory`… read-only; `clean`, `undo`, `purge`, `sort` writable with journal
  and quarantine; `review`, `review-sort`, `places` publish their port.
- The script header says in one line how to load it (`. .\mh.ps1`, or add it to
  `$PROFILE`) and how to add a folder (run `launcher` again with one more `-v`).
- Once `mh` exists, every "What next" can say `mh clean`: detect it (an env var the
  launcher sets, e.g. `MEDIA_HYGIENE_LAUNCHER=1`) and print the short form.
- Guides: the long `docker run` appears once (to create the launcher); every step below
  is `mh audit`, `mh clean`, `mh review`… Keep a collapsed "without the launcher" block.

## Acceptance

- e2e: generate the script, run `mh audit` from it (bash flavour in CI).
- Guides en and fr rewritten; `test_documentation.py` passes.
