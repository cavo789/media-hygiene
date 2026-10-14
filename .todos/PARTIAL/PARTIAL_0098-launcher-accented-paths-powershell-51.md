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

## Verified on Windows (2026-10-12, review 0056)

Windows PowerShell 5.1, `docker run --rm -v "C:\Photos\Vidéos:/data/c/Photos/Vidéos:ro"
media-hygiene --locale fr launcher > C:\Temp\cfg\mh.ps1`: the file holds two wrong characters
where each `é` was, in the `-v` line (`C:\Photos\Vid??os:/data/c/Photos/Vid??os`) and in the
French comments (`m??me`, `?? $PROFILE`); Notepad does not even recognise the encoding. Same
code page decoding seen on `config` output piped to `Select-String` (`├Ç v├®rifier`).
**Confirmed for 5.1.** PowerShell 7 too (same day, `pwsh`, `> mh7.ps1`): a clean UTF-16 LE
file, but `-v "C:\Photos\Vid├®os:/data/c/Photos/Vid├®os${mode}"` and `├á $PROFILE`, `m├¬me` in
the comments. Both shells corrupt it: the ASCII-only script is needed for both.

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

## Seen on the maintainer's machine (2026-10-13)

The `mh.ps1` written by `launcher` showed `├á` for `à` and `m├¬me` for `même` in its comments
when opened on Windows (UTF-8 bytes read in the console's old code page, CP850). Only comments
were hit there, but an accented folder in a `-v` would be corrupted the same way: the symptom is
confirmed, the fix (an ASCII-safe script, or a BOM) is still to choose. The maintainer fixed those
two comments by hand.

## Status — PARTIAL (2026-10-14)

### Done
- Fix chosen: an ASCII-only `mh.ps1`, no BOM. A BOM would not help: the corruption happens
  before `>` writes the file, when PowerShell decodes the tool's output with the console's code
  page. New `services/launcher_ascii.py`, applied by `launcher.render_script` to the PowerShell
  script only. In code lines, every non-ASCII character becomes `$([char]0x00E9)`, or
  `$([char]::ConvertFromUtf32(0x…))` beyond U+FFFF. Every path and option of the template lies in
  a double-quoted string, where PowerShell expands it. In comment lines, accents are dropped
  (NFKD, `à` → `a`). The bash script is unchanged (UTF-8 end to end).
- Tests `tests/unit/test_launcher_ascii.py`: `C:\Photos\Vidéos` and `D:\Été 2019`, French
  header, render an ASCII-only script whose strings, expanded the way PowerShell does, give back
  the exact `-v` lines; an emoji folder; bash keeps UTF-8.
- Docs en + fr: a "Good to know" bullet in `commands/launcher.md`, and a troubleshooting entry
  (`mh` mounts an empty folder instead of an accented one: write `launcher` again).

### Not done
- Manual check on Windows PowerShell 5.1 (and 7) with an image built from this commit: `docker
  run … -v "C:\Photos\Vidéos:/data/c/Photos/Vidéos:ro" … launcher > mh.ps1`, then `. mh.ps1`,
  `mh audit` finds the files of the accented folder, and `notepad mh.ps1` shows ASCII.
  **Reason:** no Windows in the devcontainer; only the maintainer can run it. Close as DONE
  once it passes.
