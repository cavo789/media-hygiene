# 0837 — Ctrl+A on a search showing its first files: say it, offer every file found

- **Priority**: High
- **Batch**: tiles
- **Depends**: none
- **Files**: `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/pick_slideshow.js.j2`, `src/media_hygiene/review/templates/pick_bar.css.j2`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/library.md`, `documentation/fr/commands/library.md`

## Reported (maintainer, 2026-11-15)

`/library`, 2026: "344 found; the first 240 shown". Ctrl+A then ▶ Slideshow: the show had
240 photos and the maintainer did not notice only 240 were picked. They did not know
either that ▶ with **nothing picked** shows every file found. Proposed: after Ctrl+A,
a small notification "You picked 240 photos of 344 (only 240 were shown, the rest on the
next pages); pick them all?".

## Today (read)

- A *Pick all {total} files found* button (`#pickAll`, `pick_grid.js.j2:208`) already
  appears in the bar once every shown file is picked on a partial search — not seen.
- 0833 (PARTIAL, same lot) made the slideshow alone treat "every shown file picked" as
  "every file found": the menu then counts 344. Other actions (Move, Album, Describe…)
  still act on the 240 picked. Two meanings of Ctrl+A on one page: align them here.

## What

- Ctrl+A (and the *pick all shown* gesture, and Invert when it ends with every shown file
  picked) on a search showing its first files: a toast from the shared frame (`mhSay`,
  with its button) — "240 picked of 344 found (only 240 are shown). [Pick all 344]" —
  the same for every tile page using `pick_grid` (feature follows its kind). The bar's
  `#pickAll` stays, more visible (next to the count, not at the end).
- One meaning for every action: what is picked is what is acted on; *Pick all 344*
  switches to every file found for every button (`everything`). Revert 0833's slideshow-
  only rule (`showing()`): every-shown-picked = those 240, like the other buttons, now
  that the toast offers the 344. Nothing picked keeps "every file found" for the
  slideshow, and the ▶ menu's entries state it: "· 344 photos (every file found)".
- Teach it once: the ▶ Slideshow menu says in one muted line "Nothing picked: every file
  found" when nothing is picked.

## Tests

- Ctrl+A on 240 of 344: the toast with *Pick all 344*; clicking it → every button counts
  344 and sends `all`.
- Ctrl+A on a search fully shown: no toast.
- ▶ with every shown file picked sends those 240 and says 240; nothing picked → 344.
