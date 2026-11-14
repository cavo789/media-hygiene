# 0823 — People page: an *Invert* button

- **Priority**: Low
- **Batch**: tile-pages
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/pick_bar*.j2`, `src/media_hygiene/people/templates/*`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

Decided by the maintainer in the inbox of 2026-11-14 (follows `.todos/PARTIAL/PARTIAL_0716-*.md`).

## Context

Every tile page inverts the picking with `I`; on the people page `i` ignores a group
(since 0667), so the people page has no way to invert. The maintainer chose a button, not a
key change: `i` keeps its meaning.

## Proposal

An *Invert* button in the people page's bar, from the shared bar component (skill
`photo-picking-pages`: reuse the shared part, never a page-local copy); same place as the
other pages' invert entry. Listed in the ⌨ panel without a key on this page.

## Acceptance

- [ ] The button inverts the picking of the shown groups only (never what is hidden)
- [ ] `i` still ignores a group (its test unchanged)
- [ ] French string; docs EN + FR of `people`; `docs_screenshots` said
