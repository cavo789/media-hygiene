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
