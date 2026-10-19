# 0255 — Measure `mh phone` with an iPhone: HEIC conversion, Live Photos, deletion from the PC

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: 0248
- **Files**: `tests/measure/mh-measure.ps1`, `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/services/phone_plan.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`
- **Needs maintainer**: one run of step 19 with an iPhone plugged in over USB (unlocked, "Trust this computer"), about 10 minutes (*estimated*, as the Android run)

## Context

`mh phone` (0219, 0251) and `mh phone --free` (0248) were built and measured on an Android phone
(Samsung A72, 2026-10-19). Asked by the maintainer the same day: "will it work with an iPhone
too?" Not checked. What is known only from general knowledge (*to check*, not measured here):

- An iPhone appears in This PC through Shell.Application with an internal storage and a `DCIM`
  folder (`100APPLE`…): `mh phone` looks for `DCIM` within three levels, so it should find it.
- **HEIC converted on transfer**: with the iPhone's *Photos → Transfer to Mac or PC: Automatic*
  (the default, *to check*), a `IMG_1234.HEIC` may arrive as a JPEG: another name and size than
  the phone listed. `mh phone` matches what is already copied by name and size: it would copy
  everything again each time; `--free`'s SHA-256 proof would always fail (safe, but useless).
  *Keep Originals* would avoid it.
- **Live Photos**: a `.HEIC` and a `.MOV` per shot.
- **iCloud "Optimise iPhone Storage"**: the originals are not on the phone, not listed.
- Deletion from the PC may be refused by the iPhone.

## What to do

1. Step 19 of `mh-measure.ps1`: log the device's `Type`, the `DCIM` path, the extensions found,
   and for 5 HEIC files the listed name and `System.Size` against the copy's name and length
   (conversion seen or not); the iPhone's transfer setting asked to the maintainer and logged.
2. From the results: adapt `phone_plan` (a `.HEIC` listed and a `.JPG` copied: the same shot?
   or say "set Keep Originals"), the Live Photo pairs, and `--free`'s deletion way (19l–19o).
3. Docs en + fr: what is checked on iPhone, the setting to choose.

## Acceptance

- The measure run on an iPhone; `mh phone` copies only the new files twice in a row; `--free`
  either works or says clearly why not.

## Gain

`mh phone` usable by iPhone users of the family, or a clear line saying what to set — instead of
silent full re-copies (*estimated* risk, from the HEIC conversion above).
