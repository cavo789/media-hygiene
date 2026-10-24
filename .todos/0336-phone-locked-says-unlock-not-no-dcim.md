# 0336 — A phone asleep or locked: say "unlock it", not "No DCIM folder"

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/services/launcher_phone.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_launcher_phone.py`, `tests/measure/mh-measure.ps1`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`

## Why

The maintainer, 2026-10-23, home page → *Make room on the phone*, an Android phone plugged in
over USB: three tries before it worked. Each failed try printed

```text
🔒 Nothing leaves the phone before you tick it on a page and press Delete; each file is first proven on the PC by its content.
No DCIM folder on <phone>: no photo to copy.
```

then went back to the home page. The cause, found by the maintainer: **the phone was asleep
(screen off / locked)**. Windows still lists the phone by name, but an Android phone shows no
storage over USB (MTP) until it is unlocked, so `mh_phone.ps1.j2` finds no `DCIM`
(`if (-not $dcim) { Write-Host "{{ t.no_dcim }}"; return }`) and says something false: the phone
has a DCIM folder. "You have to know it" — the tool must say it.

## What

1. **Tell the cases apart** where `mh_phone.ps1.j2` looks for `DCIM` (walk at line ~135): the
   phone is seen but shows **no storage at all** (no top folder: asleep, locked, or USB set to
   *Charging only*) vs a storage without `DCIM` (a real phone with no camera folder, rare).
   To check on the maintainer's phone first: what `Shell.Application` lists for a locked phone
   (no item? an empty "Internal storage"?) — a step in `tests/measure/mh-measure.ps1` (the
   phone plugged in, locked then unlocked), PowerShell 5.1, ASCII.
2. **No storage seen**: say what to do, one line each, and wait instead of leaving:
   "The phone answers but shows no storage: wake it up and unlock it, then choose *File
   transfer* in the USB notification (iPhone: *Trust this computer*)." Then poll for a short
   time (every 2 s, up to ~60 s, a setting only if the maintainer wants one), going on as soon as
   the storage appears; Ctrl+C or the time limit ends it with the same line as today's "No phone
   seen". From the home page: back to it only after that.
3. The same check for **the phone falling asleep during a long copy or deletion** (`unplugged`
   today says "unplugged?"): add "or asleep: keep it unlocked, screen on, during the copy" to
   that line, and say it up front in the estimate line ("keep the phone unlocked").
4. `No DCIM folder` stays only for a storage really without `DCIM`.

## Tests

`test_launcher_phone.py` (rendered script): the three messages exist, the wait loop is bounded,
the no-storage branch does not print `no_dcim`. The real behaviour of a locked phone: the
`mh-measure.ps1` step, results read back as the rules say.

## Docs

The launcher page's `mh phone` section, both languages: "keep the phone unlocked, screen on,
File transfer" among the first steps, and the new message.
