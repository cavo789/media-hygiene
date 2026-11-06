# 0616 — Disk space page: a Purge button, its files shown first

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0539 (DONE), 0586
- **Files**: `src/media_hygiene/review/`, `src/media_hygiene/services/`

## Why

Review of PR #62/#63 (0539): the page lists the quarantine runs and links to History; the maintainer wants a direct *Purge* button.

## What

A *Purge* button per run on `/disk-space/`, run through the background writing route of 0586. It first shows the run's files (the `/quarantine/?run=` page of 0591) and states the count and size it frees; the result is read back from disk.

## Done when

Purging from the page frees the space stated, read back; no purge without the files shown first (test).
