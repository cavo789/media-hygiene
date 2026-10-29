# 0488 — Search: a period from two cards' days, and ◀ ▶ to step through the days

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/search.html.j2`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`

A click on a card's day already searches that day (From = To = it, 2026-10-29), a click on
its folder that folder, and Back restores the search before. Two more shortcuts for sorting,
agreed with the maintainer the same day:

- **Shift+click on a second day**: the first click set From; a Shift+click on another card's
  day sets To (the two put in order), then searches: a weekend, a trip, a party past
  midnight. Same in the large view (`infoLink`).
- **◀ ▶ beside From/To**: the period moves by its own length (one day → the day before or
  after; a month chosen by 📅 → the month before or after), then searches. Disabled while
  both are empty. Sorting day by day without reopening the two calendars (about 4–6 clicks
  each time today, estimated → 1).

Done when: both work on the cards and in the large view, Back still gives each step back,
documentation in both languages, `docs_screenshots` flagged if a capture shows the form.
