# 0782 — The quarantine page says how many of its files exist nowhere else

- **Priority**: Low
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/quarantine.html.j2`, `src/media_hygiene/review/templates/quarantine.js.j2`, `src/media_hygiene/services/quarantine_pick.py`, `src/media_hygiene/services/disk_only.py`

Left by 0775 (from 0688). To do once PR #80 (one tile view on 12 pages, which touches
`quarantine.html.j2`) is merged: the run of 2026-11-12 held every tile page back for it.

## Context

The figure of the files set aside that exist nowhere else is now on the home card (0689), in
`purge` and on its page before *Purge* (0699), in `mh push`'s plan and per run on the *Disk space*
page (0775, `disk_only.only_by_run`, counted from the index). The quarantine page (`mh undo
--pick`, a tile page) lists the runs without it.

## Proposal

- Each run of the page's *Runs* list says *N exist nowhere else* (from `only_by_run`: one index
  query per run, no stat per file); the status line the total.
- Load the `photo-picking-pages` skill first: the figure sits in the shared places, nothing else of
  the page changes.

## Acceptance

- [ ] Test: a near duplicate set aside is counted in its run's line, an exact copy is not; no
      index: no figure, no error
- [ ] Docs EN + FR (`commands/undo.md`, the quarantine page)
