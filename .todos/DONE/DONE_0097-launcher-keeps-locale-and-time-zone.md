# 0097 — `mh` forgets the language and the time zone given to `launcher`

- **Priority**: High — every French reader of the quick guides gets an English tool
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/next_command.py`, `src/media_hygiene/cli/cmd_launcher.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `tests/unit/test_launcher.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`

## Context

UX review of 2026-10-12 (a beginner following the French guides). The French docs write the
launcher with `cavo789/media-hygiene --locale fr launcher > mh.ps1`, then use `mh audit`
everywhere (`documentation/fr/clean/quick-guide.md` step 1, step 7 expects *Rien à nettoyer*).
But the generated function only carries `MEDIA_HYGIENE_*` environment variables and `TZ`
(`next_command.environment()`): the global `--locale fr` option of the `launcher` run is lost.
`mh audit` then speaks English, while the page in front of the reader quotes French output.
Checked: the rendered `mh.sh` holds no locale at all.

The time zone has the same gap: the launcher keeps `TZ` only when the user passed `-e TZ=…` to
the `launcher` run, which no guide does. Every `mh` run is then in UTC: report folder names and
times are one or two hours off, a confusing first impression ("the report is from 08:00, I ran it
at 10:00").

## Goal

- `launcher` writes the effective locale into `mh` when it is not the default (as
  `-e MEDIA_HYGIENE_GENERAL__LOCALE=fr`, or as `--locale fr` before `@args`); a locale set in
  `config.toml` still wins as usual.
- The launcher commands of the guides pass the time zone: PowerShell can find it itself
  (`[System.TimeZoneInfo]::TryConvertWindowsIdToIanaId` on PowerShell 7; otherwise document
  `-e TZ=Europe/Brussels` next to `--locale fr`). Or `launcher` prints a ⚙️ line when `TZ` is
  missing, saying how to add it, so the script is not written blind.
- `launcher` ends with one line saying what `mh` will remember: folders, language, time zone.

## Acceptance

- Unit test: `--locale fr launcher` renders a script that runs the tool in French; the default
  locale adds nothing.
- The French quick guides (clean and sort) produce French output with `mh`, as their text says.
