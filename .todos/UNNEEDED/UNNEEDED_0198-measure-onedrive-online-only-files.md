# 0198 — `mh-measure.ps1` step 18: OneDrive online-only files, as the container reads them

- **Priority**: High — the guard of 0199 cannot be designed without it
- **Batch**: launcher
- **Depends**: —
- **Files**: `tests/measure/mh-measure.ps1`

## Context

Chosen by the maintainer on 2026-10-17 from the competitor research (proposal A2, the OneDrive
guard). Windows 11 turns on OneDrive's backup of Desktop, Documents and Pictures during setup with
a Microsoft account (reported in June 2024 by Neowin and others; some readers doubted it: to keep
in mind). With Files On-Demand, a photo can live in the cloud only: Explorer shows its full size,
nothing is on the disk.

How Docker Desktop's file sharing reads such a placeholder is not documented (searched on
2026-10-17: nothing from Microsoft or Docker). Two outcomes are possible, and the guard differs:

- the read downloads the file: a first audit downloads the whole library (tens of GB, the disk may
  fill up);
- the read fails: the audit then reports an unreadable file, which `clean` sets aside as broken —
  for a placeholder, a move that OneDrive may turn into a deletion in the cloud.

The troubleshooting page (`## OneDrive "Files On-Demand"`, both languages) already says
"Analysing a folder whose files are online-only downloads them all": written with the step-by-step
documentation, never measured. The step checks it; the docs follow what it shows.

Measure first, on the maintainer's PC (or any PC with OneDrive); 0199 builds the guard from the
results.

## What to do

A step 18 in `tests/measure/mh-measure.ps1`, run with `-Only 18`. Same rules as the other steps:
Windows PowerShell 5.1, ASCII only, no `-ExecutionPolicy Bypass` (Avast, 2026-10-16), results
logged with `Log` into the measures file.

1. Find OneDrive: `$env:OneDrive`, else `$env:OneDriveConsumer` / `$env:OneDriveCommercial`. None:
   log `18. skipped: no OneDrive on this PC` and end the step.
2. Ask before writing anything into OneDrive (`Read-Host`, y/N). Copy 5 photos of `-Photos` into
   `<OneDrive>\mh-measure-18`. Wait until OneDrive has uploaded them (poll their attributes every
   5 s, 3 minutes at most; log what was seen). Then free them up as Explorer's "Free up space"
   does (`attrib +U -P`), and wait until they are placeholders. Log each file's attributes as an
   integer and as names (e.g. `0x00500020`, and whether `Offline` 0x1000 and
   `RecallOnDataAccess` 0x400000 are set): the guard will test whichever Windows sets.
3. Audit that folder through `Measure-Mh`, the photos `:ro`, with a cache volume of its own
   (removed at the end). Log: exit code, wall time, and the lines about unreadable or broken
   files (add their wording to `$wanted`). Then log the files' attributes again: still online-only
   means Docker's read did not download them; local means it did.
4. Ask the maintainer what the folder's OneDrive icon shows now (cloud, green tick) and log the
   answer.
5. Remove the test folder (OneDrive puts it in its recycle bin: say so) and the cache volume.

Update the step list at the top of the script and its usage lines (`-Only 18`).

## Explicit non-goals

- No change to `mh` or the tool: the guard is 0199.
- No `clean` on the placeholders: the audit's verdict is enough to design the guard, and a set-aside
  placeholder could become a deletion in the cloud.

## Acceptance

- The step runs with `-Only 18`, ends cleanly without OneDrive, asks before writing into OneDrive,
  removes what it created, is ASCII only, and is listed at the top of the script.
- DONE when the step is written: running it is the maintainer's part, recorded in 0199's
  `Needs maintainer`.

## Gain

None by itself: it turns 0199's unknowns (a download or a failure; which attribute marks a
placeholder) into one run of about 5 minutes (estimated: upload, free up and audit of 5 photos).

## Closed — UNNEEDED (2026-10-17)

The maintainer does not use OneDrive and cannot run this step. 0199 is designed instead from
Microsoft's documentation (*File Attribute Constants*, checked on 2026-10-17):
`FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` (0x00400000) marks a file "not fully present locally", and
"reading the file … will cause at least some of the file/directory content to be fetched from a
remote store". What Docker Desktop's file sharing does with such a file stays unmeasured: a
contributor with OneDrive may check it later. The risk of a failed download read as a broken file
is covered by 0222.
