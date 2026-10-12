# 0098 — `launcher > mh.ps1` in Windows PowerShell 5.1: accented folder names may be corrupted

- **Priority**: High — to verify first on Windows; if confirmed, `mh` mounts a folder that does not exist
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/launcher.py`, `tests/unit/test_launcher.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`

## Context

UX review of 2026-10-12. The guides write the launcher with `docker run … launcher >
"$HOME\media-hygiene\mh.ps1"`. In Windows PowerShell 5.1 (the default PowerShell of Windows
10/11), the output of a native program is decoded with `[Console]::OutputEncoding` (the OEM code
page, 850 or 437) before `>` writes it as UTF-16. The tool writes UTF-8: a folder such as
`C:\Photos\Vidéos` or `D:\Été 2019` (common for French users, the demo library itself has
`Vidéos`) would then land in `mh.ps1` as `Vid├®os`. `mh` would mount a folder that does not
exist; Docker Desktop creates it empty, and the audit silently misses the real one.

TODO 0039 handled the same code page issue for `decisions.json`, not for the launcher. Not
checked on Windows: there is no Windows in the devcontainer.

## Goal

1. Verify on Windows PowerShell 5.1 and 7, with a mounted folder holding `é`.
2. If confirmed: make the PowerShell script pure ASCII, whatever the console decodes. Non-ASCII
   characters of a path become `$([char]0x00E9)` inside the double-quoted strings of the
   template (PowerShell expands them), and the comment header stays ASCII. The bash script is
   unaffected (UTF-8 end to end).
3. Troubleshooting entry if a workaround is still needed for older scripts: write `launcher`
   again.

## Acceptance

- Unit test: a mount `C:\Photos\Vidéos` renders an ASCII-only `mh.ps1` whose string evaluates
  back to the original path (checked by decoding the `[char]` escapes in the test).
- Manual check on Windows PowerShell 5.1: `mh audit` finds the files of an accented folder.
