# 0834 — Slideshow: remember the people avoided, ticked by default in every show

- **Priority**: High
- **Batch**: tv-slideshow
- **Depends**: none (0829 adds the block to *On this PC*: the remembered ticks apply there too)
- **Files**: `src/media_hygiene/config/slideshow_settings.py`, `src/media_hygiene/slideshow/avoid_desk.py`, `src/media_hygiene/services/slideshow_people.py`, `src/media_hygiene/services/slideshow_avoid.py`, `src/media_hygiene/slideshow/templates/slideshow_avoid.js.j2`, `src/media_hygiene/review/templates/home_tv.js.j2`, `src/media_hygiene/review/page_settings.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Decided (maintainer, 2026-11-15) — replaces 0825's "asked each time"

"If I tick my daughters' former boyfriends, it is for good: no reason to see them in any
other show." The people avoided are **remembered** and **ticked by default** in every
show, until unticked.

## What

- Stored in `config.toml`: `[slideshow] avoid = ["Antoine", …]` (names of
  `[[people.person]]`), written from the PC like the pace default (0607: `page_settings`,
  tomlkit, read back from disk and said). Each tick/untick on the PC's remote saves it.
- Every show starts with them set out (all entries: library ▶ PC/TV, album, home TV
  choices, *On this PC* of 0829) — **visibly**: the block lists the remembered people
  ticked even when they are on no photo of this show ("Antoine — remembered, on none of
  these photos"), and their photos sit greyed / in the "Will not be shown" group (0831).
  Never a silent filter (memory `never-act-on-hidden`).
- The block's header says it in one line: "Remembered for every show: Antoine, Hugo".
- Phone (read-only, `phone-read-only`): it can tick/untick **for this show** only; the
  remembered list is changed on the PC. Say so on the phone in one line.
- A name in `avoid` no longer in `[[people.person]]` (renamed, removed): ignored and
  listed by `config tidy` (0812); a rename/merge by 0827 rewrites it.
- The home page's TV block (0825), if kept, starts from the same list (one source).

## Tests

- Ticking on the PC saves `[slideshow] avoid`, read back from disk; a new show starts with
  those photos set out and the names ticked.
- Unticking removes the name from the file.
- The phone ticks for the show only: `config.toml` unchanged.
- A remembered person on no photo of the show is listed, ticked, with "on none of these photos".
