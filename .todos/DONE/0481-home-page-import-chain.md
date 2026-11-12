# 0481 — The import chain on the home page (rest of 0480)

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/` (home page), `src/media_hygiene/review/home_app.py`, `src/media_hygiene/config/import_settings.py`

## Why

0480 item 4: after `mh import --phone` the chain (audit → copies → bursts → tags → places →
slideshow) runs in the console only. The maintainer wants it on the home page too.

## What

- The chain followed live on the home page, step by step.
- A chain stopped halfway offered again from the next step.
- Steps switched on/off from the list, saved in `[imports] then` (tomlkit, comments kept,
  atomic), read back and shown.
- Period buttons *Today · This week · This month · All* (as `--since`).

## Acceptance

Switching a step off on the page writes `[imports] then`, read back; an import stopped after
`copies` resumes at `bursts`.

## Status — PARTIAL (2026-11-03)

### Done
- Steps switched on/off from the home page, under *Copy the new photos of the phone*: one box
  per step, saved in `[imports] then` (`review/import_steps_api.py`, `toml_edit`: comments
  kept, atomic), read back and shown. Tests: `tests/unit/test_import_steps_api.py`.

### Not done
- The chain followed live on the home page, a chain stopped halfway resumed from the next
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  step, the period buttons (*Today · This week · This month · All*).
  **Reason:** the chain runs in `mh.ps1` on the host (PowerShell), not in the container: a
  live follow needs each step to write its progress where the home server reads it (a chain
  state file under `/cache` or `/journal`, written by `phone-end` and `mh.ps1`), and the
  resume needs `mh.ps1` to start from a given step. A design of its own (which file, who
  writes it, what a stale one means); the period buttons only make sense once the chain can be
  started from the page.

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
