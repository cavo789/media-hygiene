# 0590 — import shows the new files as photos before copying them

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0524 (DONE)
- **Files**: `src/media_hygiene/services/import*`, `src/media_hygiene/cli/cmd_import*.py`, `src/media_hygiene/search/`, `documentation/en/commands/import.md`, `documentation/fr/commands/import.md`

## Why (inventory of 0524)

`mh import` and `mh import E:\DCIM` copy into the library files the user only sees as a count; the
audit's `_backups` section lists their paths as text. Only the phone has a page of photos.

## What

A page of tiles (`photo-picking-pages`) of what only the folder holds, offered first; the console
verb stays the fast path, saying in one line what it skips. Mounts: the folder is read-only.

## Done when

The new files of a backup folder or a plugged-in folder can be seen and unpicked before the copy
(test); the page offers it first on the home page and in 👉 What next.
