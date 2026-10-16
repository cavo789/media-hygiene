# 0190 — mh shortcut and mh explorer: say why a write failed, no "double-click" after a failure

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher_host.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_launcher_comfort.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`

## What was seen (measured on the maintainer's Windows 11, PowerShell 5.1, 2026-10-16)

`mh shortcut`, from a normal PowerShell, `mh` written by the local image built from `main`:

```
Impossible d'écrire C:\Users\Christophe\Desktop\Media Hygiene.lnk.
Impossible d'écrire C:\Users\Christophe\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Media Hygiene.lnk.
Double-cliquez sur Media Hygiene sur le Bureau ou dans le menu Démarrer : le menu de mh s'ouvre.
```

Two defects:

1. **The reason is swallowed**: `try { $link.Save() } catch { }` in `_mh_shortcut` (and the same
   empty `catch` in `_mh_explorer`). The same `Save()` typed by hand said
   `UnauthorizedAccessException`: Avast had locked that one path after a detection raised by the
   measure harness (step 10b of `tests/measure/mh-measure.ps1`); another `.lnk` name on the same
   Desktop, even with `-ExecutionPolicy Bypass` in its arguments, saved fine; a reboot lifted the
   lock, then `mh shortcut` wrote and read back both shortcuts with no alert.
2. **The closing line tells the user to double-click an icon that does not exist**: the
   `shortcut` text is printed whatever happened.

## Fix

- Keep the exception's message (`$_.Exception.InnerException.Message` or `.Message`, the COM
  wrapper hides the useful one: to check which) and print it on the `not_saved` line, one line,
  no PowerShell error record (the CLI never shows a traceback).
- One hint line when the error is an access refusal: an antivirus may lock a path it flagged;
  restarting Windows lifts such a lock (measured with Avast only; say "an antivirus", no brand).
- Print the "double-click" line only when at least one shortcut was read back from disk; same
  rule for `explorer` (it already reads back, check its failure wording).
- Unit tests on the rendered script (the texts and the branch), as the existing ones in
  `tests/unit/test_launcher_comfort.py`; both languages of `launcher.md` if the output shown there
  changes (then `docs_screenshots` is stale: say it, do not run it).

## Out of scope

The `-ExecutionPolicy Bypass` in the shortcut and the right-click command: measured harmless here
(the `.lnk` with it saved, no alert from a user-like run), so it stays.
