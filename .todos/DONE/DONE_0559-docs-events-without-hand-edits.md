# 0559 — Documentation: events made on the pages, config.toml never edited by hand

- **Priority**: Critical — goes with 0556–0558
- **Batch**: events
- **Depends**: 0556, 0557, 0558
- **Files**: `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`, `documentation/*/sort/quick-guide.md`, `src/media_hygiene/config/templates/config.toml.j2`

## What

- Rule decided with the maintainer (2026-10-31): `config.toml` is never edited by hand,
  whatever the case; the docs show the page gestures only (search a period → *Move to an
  event…*; accept the events found in your folders; late photos proposed).
- Explain two events on the same days (a daughter elsewhere) and how their devices separate them; refusals in `/config/events/`; the same name in several years (`Turin`) is several events.
- The `date_range` example in `config.toml.j2` becomes a comment saying the page writes
  events; both languages; say that `docs_screenshots` should run (never run it unasked).
