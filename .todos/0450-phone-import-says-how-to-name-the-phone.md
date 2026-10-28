# 0450 — `mh import --phone`: say how to give the phone a name of its own

- **Priority**: Low
- **Batch**: import
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/services/launcher_phone_say.py`, `src/media_hygiene/services/launcher_phone.py`, `documentation/en/commands/import.md`, `documentation/fr/commands/import.md`

## Why

The maintainer, 2026-10-28: copies should go to a folder per person (*Christophe A71*, *Manon
S23*). They already do: `Phone\<name>` (soon `From phone\<name>`, 0441) uses the name Windows
shows in *This PC*, which is the phone's own *device name*. Left at the factory name (*Galaxy
A71*), two phones of the same model share a folder.

## What

- Docs en+fr (`commands/import.md`): the copies go to a folder named after the phone; to tell
  phones apart, rename each one (Samsung: *Settings › About phone › Edit*; Pixel: *Settings ›
  About phone › Device name*), then plug it in again.
- The console: when the name looks like a factory name (it starts with a brand or model word:
  *Galaxy*, *Pixel*, *iPhone*, *Redmi*…, a named constant list), one 💡 line says how to rename it.

## Explicit NON-goals

- Renaming existing folders.
