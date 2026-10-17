# 0218 — `mh-measure.ps1` step 19: a phone plugged in over USB, read from PowerShell (list, copy 20 files)

- **Priority**: High — the phone import of 0219 is designed from what this step shows
- **Batch**: launcher
- **Depends**: —
- **Files**: `tests/measure/mh-measure.ps1`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F9): "we plug our smartphone in and copy 100 % of
the photos and videos each time; it would be great to copy only the new ones". A phone plugged in
over USB shows in Explorer without a drive letter (MTP): Docker cannot mount it, but Windows
itself can read it, and so can PowerShell through the Shell's COM object, the one `mh shortcut`
already uses. Scripts doing so exist (2026-10-17: the `ipad-to-nas` scripts on GitHub, a Microsoft
forum thread; they move files, never what we want), so it is feasible, but the details vary with
the phone and the Windows language, and nothing of it can run here: measure on the maintainer's
phones first.

Known from a Microsoft answer (2026-10-17): a copy from an Android phone through Explorer keeps the
*modified* date of the photo and sets the *created* date to the copy's time.

## What to do

A step 19 in `tests/measure/mh-measure.ps1`, run with `-Only 19`: Windows PowerShell 5.1, ASCII
only, no `-ExecutionPolicy Bypass` (Avast, 2026-10-16), results logged with `Log`. **It never
deletes, moves or renames anything on the phone** (`CopyHere` only, never `MoveHere`).

1. Ask to plug the phone in and unlock it (Android: choose "File transfer"; iPhone: "Trust this
   computer"); press Enter.
2. `(New-Object -ComObject Shell.Application).Namespace(17)` ("This PC"): log every item that is
   not a file-system folder (name, `Type`, `IsFileSystem`); the maintainer picks the phone by
   number.
3. Find `DCIM` on it (case ignored, at most three levels down: Android's "Internal shared storage",
   localized; iPhone's "Internal Storage"); log the path found, and the other top folders
   (`Pictures`, `Movies`, `WhatsApp`…) by name only.
4. List `DCIM` recursively: count of files, time taken, the extensions seen (iPhone: HEIC or JPG,
   depending on its "Transfer to Mac or PC" setting), and for 10 files every property
   available: `Name`, `Size`, `ModifyDate`, `ExtendedProperty('System.Size')`,
   `ExtendedProperty('System.DateModified')`, `ExtendedProperty('System.DateCreated')`.
5. Copy the 20 most recent files into a temporary folder under `-Work` with
   `CopyHere(item, 4 + 16 + 1024)` (no progress dialog, yes to all, no error dialog). `CopyHere`
   returns at once: wait for each file by polling the target folder until a file of that name has
   the size the phone said (60 s at most each); log the time per file, the MB/s, and any file that
   never arrived; then the created and modified dates of the copies against the phone's.
6. Copy the same 20 again: log whether Windows asks anything (it must not, with flag 16) and what
   happens to the existing copies.
7. Remove the temporary folder; say that the phone is untouched.

Update the step list at the top of the script and its usage lines (`-Only 19`).

## Explicit non-goals

- `mh` itself: 0219.
- Wi-Fi transfers, Google Photos, iCloud: other ways in.

## Acceptance

- The step runs with `-Only 19`, never writes to the phone, cleans up, is ASCII only, and is
  listed at the top of the script.
- DONE when the step is written: running it is the maintainer's part, recorded in 0219's
  `Needs maintainer`.

## Gain

None by itself: it gives 0219 the device names, the `DCIM` path, the properties that say a file's
size and date, how to know a copy is finished, and the speed — in one run of a few minutes
(estimated: 20 files).
