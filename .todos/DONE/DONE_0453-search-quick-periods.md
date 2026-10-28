# 0453 — Search: To follows From; one click for today, this month, this year

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

The maintainer, 2026-10-28: filling *From* then *To* by hand for a recent day is slow; *To*
should take *From*'s day when empty or earlier; buttons for today, the month, the year, with
little text.

## What (done)

- *From* changed: *To* = *From* when empty or earlier.
- Under the dates: 📍 Today, 🗓️ Month, 📆 Year, ✕ (any date), each with its full words as
  title and `aria-label`; a click fills both fields (local days) and searches.
