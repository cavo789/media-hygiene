# 0638 — A dropped tag no longer finds a photo through the model's caption

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/`

## Problem

Follows 0546 (commit d8e53d5e). After dropping `panneau de signalisation`, a quoted search for
it still finds the photo through the model's sentence (source `caption`).

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

A dropped tag no longer brings a photo back, by any source: the search skips the caption match
for a stop word.

## Acceptance

- [ ] Dropped tag, quoted search: the photo is not found through its caption (test)
- [ ] Restored tag: found again
