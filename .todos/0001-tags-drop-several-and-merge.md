# 0001 — Tags: drop several at once, merge a synonym into another tag

- **Priority**: Low
- **Batch**: search
- **Depends**: 0546
- **Files**: `src/media_hygiene/search/`, `src/media_hygiene/review/`

## Why

Left out of 0546 by the maintainer's choice (2026-11-06): its first version drops one tag at a time.

## What

A list of the most frequent tags to tick and drop together; "merge into another tag" for synonyms (`panneau` → `panneau de signalisation`). The photos concerned are shown first, the count stated on the button.

## Done when

Several tags dropped, or one merged, read back from disk; the XMP sidecars follow (tests).
