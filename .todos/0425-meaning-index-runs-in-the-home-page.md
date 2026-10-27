# 0425 — Search by meaning: its index built from the home page, as `tags` does

- **Priority**: Low
- **Batch**: home
- **Depends**: 0424
- **Files**: `src/media_hygiene/cli/meaning_flow.py`, `src/media_hygiene/services/home_tags.py`, `src/media_hygiene/review/templates/home_tags.js.j2`, `documentation/en/commands/tags.md`, `documentation/fr/commands/tags.md`

## Why

Survey of 0421 (2026-10-27). `tags --meaning` (opt-in) runs a model on the processor over every
photo, read-only on the photos, writing the cache: *estimated* in the same range as the face scan
per photo (a CPU model, no GPU), so hours on a full collection, in a minimised console.

## What

After `tags` in the page, a third half: *Build search by meaning* with its figures, progress,
Stop — on the runner 0424 shares. Only when `[tags] meaning = true`.

## Not moved (the rest of the survey)

- `inventory`: 0.39 s on the demo tree (28 files, 0.25 s of it the start; measured 2026-10-27,
  `hygiene inventory`), read from the index alone: seconds on 52,000 files (estimated) — stays a step.
- Phone import: it writes into the photo folders, so it is not a read-only step: it belongs to
  0361 (writes run as steps by `mh`, followed live).
