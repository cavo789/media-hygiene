# 0247 — `mh-measure.ps1` step 19, extended: delete a file on a phone over USB (MTP), and the real copy speed

- **Priority**: Medium — 0248 (free the phone) is designed from what this step shows
- **Batch**: launcher
- **Depends**: —
- **Files**: `tests/measure/mh-measure.ps1`

## Context

Asked by the maintainer on 2026-10-19: `mh phone` should also free the phone (0248). Step 19
(0218) only reads the phone; 0219's import never writes to it. Nothing tells yet how Windows
deletes a file on a phone through `Shell.Application`, nor whether it asks: step 19 showed that
`CopyHere` opens its "replace" dialog **behind the console** despite flag 16 (386.3 s for 20
files, a person answering each one, measured 2026-10-19). A deletion that waits for a hidden
dialog, or that asks nothing at all, are both to know before 0248 is written. There is no
recycle bin over MTP (to check on the phone: does a file deleted from the PC go to the Samsung
Gallery's trash?).

The step's first run (2026-10-19) also had the size read as 0 (`.Size` over MTP): the copy speed
was not measured. That is fixed in step 19 since (`PhoneSize`, `PhoneDate`).

## What to do

New parts of step 19, after 19f, each said before it runs ("this writes ONE test file to the
phone, then deletes it"), and asked once (`y` to go on, anything else skips them):

- **19h** write a test file to the phone: a small synthetic JPEG made by the script (never a
  photo of the maintainer), named `mh-measure-<stamp>.jpg`, copied with `CopyHere` into the
  phone's `DCIM` (a subfolder `mh-measure` created there with `NewFolder`). Log whether it
  appears, its `System.Size`.
- **19i** delete it with `$item.InvokeVerb("delete")`: log the time, whether a dialog showed
  (ask the maintainer, with the Alt+Tab hint of 19f), whether the item is gone when the folder
  is listed again. Then write a second test file and try the other ways, each logged the same:
  `InvokeVerbEx("delete")`, and `MoveHere` of the phone's file into the temporary folder of the
  PC (is the phone's copy gone after? does a dialog show?).
- **19j** remove the `mh-measure` folder of the phone (the same way that worked), and list the
  phone's `DCIM` again: only the test files changed, every other file still there (count before
  and after, logged).
- **19k** the read speed for the proof of 0248: copy the 20 files of 19d once more into an
  **empty** folder (no dialog), waited for by `PhoneSize`, then `Get-FileHash -Algorithm SHA256`
  of each: MB/s of the copy, MB/s of the hash.
- Ask the maintainer to look at the phone's gallery: are the test files in its trash?

## Explicit non-goals

- Any file of the phone but the two test files: never touched.
- iPhone: the step logs what it does on one if plugged, nothing is designed for it here.

## Acceptance

- `-Only 19` runs every part; the deleting parts only after the `y`; ASCII only; listed at the top
  of the script and in its usage lines.
- DONE when the step is written: running it is the maintainer's part, recorded in 0248's
  `Needs maintainer`.

## Gain

None by itself: it gives 0248 the way to delete without a hidden dialog, and the time the proof
(reading back each file) costs — in one run of a few minutes with the phone plugged in.
