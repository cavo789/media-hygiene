# 0312 — Freeing a phone: the page groups the files by the phone's folders, one tick per folder

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/review/phone_views.py`, `src/media_hygiene/review/phone_tiles.py`, `src/media_hygiene/review/phone_app.py`, `src/media_hygiene/review/templates/phone_review.html.j2`, `src/media_hygiene/review/templates/phone_review.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `tests/integration/test_phone_review.py`

## Why

The maintainer, 2026-10-23, on the page of `mh phone --free` (screenshot shared in the
session): one wall of tiles, grouped by *why* the PC holds them (📚 library, 📥 copied by
`mh phone`, ⚠️ set aside — `GROUPS` in `phone_views.py`). They sorted their photos into folders
on the phone and think in those folders: "keep everything in the folder named *Surricate*"
should be one click, not hundreds of unticks.

## What

1. **Groups = the phone's folders** (`PhoneTile.folder`, below `DCIM`), in the order of the
   phone's folder names, each with its count and size ticked (`{ticked} of {count} ticked ·
   {size}`, already translated). The reason the PC holds a file (library / import) becomes a
   small badge on its tile; the help texts of today's groups move to a legend at the top.
2. **One box per folder**: ☑ ticks every file of the folder, ☐ unticks them all, ▣ when
   mixed. One `POST /api/phone` with every choice (the API already takes several), saved and
   read back as for one file.
3. **Set-aside files stay apart**: a folder's ☑ never ticks a file set aside before on purpose
   (it needs its own confirmation, its warning); the folder's line says "N set aside, not
   ticked". Keep them visible inside their folder, with their warning.
4. Long folders: each folder can fold (closed state per viewer in `localStorage`, try/catch).

To check first: whether `mh phone` lists only `DCIM` (`phone_plan.py` says "below DCIM"); a
folder made by a gallery app (`Pictures/Surricate`) may live outside it. If so, say it in the
page's legend and file a follow-up rather than widening the import here.

## Tests

- `phone_groups` with files of three folders, one holding a set-aside file: three groups in
  name order, the set-aside counted apart.
- `POST /api/phone` with a whole folder unticked: the file read back holds none of its ranks.

## Docs

The launcher page's section on freeing the phone (both languages); `docs_screenshots`
should run afterwards (not unasked). The selection gestures of `browse` (rectangle,
Shift/Ctrl, invert, keyboard panel) are 0314, built on these groups.
