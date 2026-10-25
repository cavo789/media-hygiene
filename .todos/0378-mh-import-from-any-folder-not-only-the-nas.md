# 0378 — `mh import <folder>`: any folder (NAS, USB disk, SD card, old disk), words not only about the NAS

- **Priority**: Medium
- **Batch**: import
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_import.py`, `src/media_hygiene/services/import_plan.py`, `src/media_hygiene/services/import_run.py`, `src/media_hygiene/services/policy.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/menu_catalog_import.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/import.md`, `documentation/fr/commands/import.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`

## Why

The maintainer, 2026-10-25: `mh import` brings in the photos and videos the library lacks,
matched by content (SHA-256) whatever their name or place, and leaves out what the user set
aside. Nothing in that is about a NAS: it already reads any folder added with
`mh folders add --backup` (a NAS, a USB disk, an old disk, a synced cloud folder). But its words
are all about the NAS, misleading for a USB disk:

- the destination `From NAS` (`import_plan.FROM_BACKUP`);
- the help of `cmd_import.py` ("what only a backup (a NAS) holds"), the menu ("Get back what only
  the NAS holds"), the title of `commands/import.md` ("ce que seul votre NAS contient").

And a folder must be declared a backup first: `mh import E:\` (an SD card, a friend's disk) is
not possible.

## What to do

1. **`mh import [<folder>]…`**: without a folder, the compared backups as today; with one
   (host path, as the Explorer shows it), that folder only, mounted `:ro` for this run by `mh`
   (like a backup, `launcher_backups.py`), without adding it to `mh.ps1`. The audit with it, the
   same plan, the same checks, the same `undo`.
2. **Destination named after the source**: `From <name>` — the NAS share's name, the drive's
   volume label or letter for a disk (`From E`, *to design*: label read by `mh.ps1`?), in the
   first photo folder; `--to` unchanged. A folder `From NAS` already filled by an earlier import
   stays where it is (the index knows its files: they are held, not imported again; test it).
3. **Words**: help, menu (keywords keep `nas`, add `usb disk card sd`), page en + fr reworded for
   "a folder: your NAS, a USB disk, an SD card, an old disk", with the NAS as the first example
   only; the line saying it is not `mh pull` (0376: puts back what `push` sent, at its place).
4. `i18n_update` + French; `docs_screenshots` to run (said, not run).
5. Tests: an import from a folder not declared as backup; the destination name per source; an
   earlier `From NAS` folder not imported twice.

## Acceptance

- `mh import E:\DCIM` copies into `C:\Photos\From E\…` (or the chosen name) only what the
  library lacks; nothing written to `E:`.
- No user-facing string of `import` says "NAS" except as an example.

## Gain

`import` usable for an SD card or a USB disk in one command (today: `folders add --backup`,
`audit`, `import`, then remove the backup: 4 steps, *counted* from the docs), and words that do
not mislead.
