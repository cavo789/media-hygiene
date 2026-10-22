# 0298 — One notion of album: the hard-link folder of `album` becomes an export of a logical album

- **Priority**: Medium — two different things are called "album" since 0295
- **Batch**: share
- **Depends**: 0295
- **Files**: `src/media_hygiene/cli/cmd_album.py`, `src/media_hygiene/services/album.py`, `src/media_hygiene/services/album_folder.py`, `src/media_hygiene/services/albums.py`, `src/media_hygiene/services/album_picks.py`, `src/media_hygiene/share/albums.py`, `src/media_hygiene/cli/menu_catalog_share.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/album.md`, `documentation/fr/commands/album.md`

## Context

The `album` command (older) gathers a selection into a folder of **hard links** ("Christmas",
"My best photos": one photo in several folders, no extra space; `--apply`, journaled, undone by
`undo`). 0295 (2026-10-22) added **logical albums**: named lists in `/reports/albums.json`,
filled from search, browse and the burst review, shown on the TV, prepared for sending (0296),
shown on a phone (0297). Found by 0295's subagent: two notions, one name.

## Decided (2026-10-22, by the maintainer, `/todo:iterate`)

**Merge them**: one album, the logical one (`albums.json`). The hard-link folder becomes one
more way to use an album, next to *Prepare for sending*: materialise the album as a folder of
hard links on the disk.

## What to do

1. `album` takes an album of `albums.json` (by name) as its selection, instead of (or besides,
   to decide: say it in the report) its own way of picking files today (`album_picks.py`);
   what it writes on the disk, its journal and `undo` stay as they are (user data: no change
   to the safety of the hard links).
2. A folder made by the old `album` before this change: still listed, still undone; whether to
   offer turning it into a logical album (read its links back) — propose, do not guess.
3. The *Share* area (0294) lists the album's uses: the TV, the phone, *Prepare for sending*,
   *A folder of links on the disk*.
4. Docs en + fr (`commands/album.md` explains the album first, then its uses), translations,
   `docs_screenshots` afterwards.

## Acceptance

- One word, one notion in the CLI, the pages and the docs (a grep of "album" in the docs reads
  consistently).
- `album "Crete 2023" --apply` makes the hard-link folder of exactly that album; `undo` removes
  it (tests on real files, `tmp_path`).
