# 0591 — purge shows the quarantine as photos first

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0524 (DONE)
- **Files**: `src/media_hygiene/cli/cmd_purge*.py`, `src/media_hygiene/services/disk_space.py`, `src/media_hygiene/cli/menu_catalog_clean*.py`, `documentation/en/commands/purge.md`, `documentation/fr/commands/purge.md`

## Why (inventory of 0524)

`purge` is the only final erase; its documentation tells the user to check the quarantine "in the
Explorer". `undo --pick` already shows a run's quarantined files as photos, but nothing offers it
before a purge, neither the step, nor the disk space page, nor the console's question.

## What

Before purging, the step and the disk space page offer that page, on the run about to go. The
console's question names it in one line.

## Done when

From *Purge*, one click shows the files of the run as photos (test); the docs say so, not Explorer.
