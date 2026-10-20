# 0248 — `mh phone`: free the phone — delete from it what the PC holds, after importing what it lacks; a set-aside photo only with a warning

- **Priority**: Medium — the maintainer's family backs their phones up to free them
- **Batch**: launcher
- **Depends**: 0219, 0247
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/services/phone_plan.py`, `src/media_hygiene/services/phone_free.py` (new), `src/media_hygiene/cli/cmd_phone_plan.py`, `src/media_hygiene/review/phone_app.py` (new), `src/media_hygiene/review/phone_session.py` (new), `src/media_hygiene/review/templates/phone_review.html.j2` (new), `src/media_hygiene/actions/remembered.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_phone_free.py` (new), `tests/integration/test_phone_review.py` (new), `tests/unit/test_launcher_phone.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `tests/measure/mh-measure.ps1`

## Context

Asked by the maintainer on 2026-10-19: "my daughters often back their phones up: the idea is to
free room on the phone". 0219 imports only the new files and never touches the phone; this TODO
adds the deletion, in three cases:

1. **On the PC and on the phone** → propose to delete it from the phone.
2. **Only on the phone** → import it (0219), then propose to delete it from the phone.
3. **Not in the library, but set aside on purpose** (a choice remembered by 0216: burst shot, near
   copy, photo chosen, unwanted; still in the quarantine or purged since) → never imported, left
   on the phone; deleting it is proposed **with a warning**, two of them (maintainer's choice):
   - still in the quarantine: "Set aside on <date>, still recoverable with `mh undo <run>` until
     `mh purge`.";
   - purged: "Purged on <date>: it is nowhere else. Deleted from the phone, it is **lost for
     good**."

An exact copy that `clean` removed is case 1, not 3: its content is kept elsewhere on the PC.
"The PC" is every folder `mh` mounts, backups (0204) included.

Decisions of the maintainer (inbox, 2026-10-19): a separate TODO from the import (0219);
**proof by content before deleting**; the choice made in a **page of the browser**; the two
warnings above.

## Measured (step 19l-19o of `mh-measure.ps1`, 2026-10-19, maintainer's Samsung A72, PowerShell 5.1, Windows Terminal)

- **`InvokeVerb('delete')` and `InvokeVerbEx('delete')` ask** "Are you sure that you want to
  permanently delete '…'?" in a dialog **behind the console**: the calls returned after 8.9 s and
  18.8 s, all of it waiting for the maintainer to find the dialog (Alt+Tab). Not usable.
- **`MoveHere` into a PC folder: no dialog**, returned after 0.1 s, the file gone from the phone
  after 0.4 s, its copy on the PC (644 bytes, intact). **The way to use**: the phone's file is
  moved to the PC, never deleted there — the moved file is itself the safety copy.
- Removing a folder (`DCIM\mh-measure`) with `InvokeVerb` asks too ("permanently remove the
  folder … and all of its contents?"), 16.1 s. Folders: `MoveHere` as well, or leave them.
- Only the test files were touched: DCIM held 801 files before and after.
- **No gallery trash**: a file removed over USB is not in the phone's Gallery → Trash. A deletion
  over MTP is final on the phone side: the PC copy, proven equal, is the only way back.
- Speeds: the 20 newest photos (93.6 MB) copied into an empty folder at 24.2 MB/s; their SHA-256
  at 770 MB/s (files just written, read from the OS cache: the proof costs nothing next to the
  copy; a cold read would be slower, *to measure* if it matters).
- DCIM listed: 801 files in 24.8 s the first time, 0.5 s just after (cached by Windows).

## What to do

- **The proof (SHA-256), never name and size alone.** The phone gives no content; name + size +
  date only make the *proposal*. Before deleting a file ticked in the page, `mh` copies it from the
  phone into an empty staging folder (0219's, no dialog), then:
  - case 1: its SHA-256 equals the digest of a file of the library that is still there now (the
    container checks: the index's digest, computed now for a candidate without a full digest;
    the PC file mounted `:ro`);
  - case 2: the import's copy, in its place, has the phone's `System.Size` and the same SHA-256
    as the staging copy, and the image check of the audit reads it (Pillow / `ffprobe`): a
    truncated copy never frees its original;
  - case 3: its digest is one the journals remember (`actions/remembered.py`: full SHA-256, or the
    partial digest when only that one was kept);
  - otherwise: **kept on the phone**, said with its reason ("not the same content as
    `2025\07\IMG_0001.jpg`").
  The proof reads each file deleted once (speed measured by 0247: say the estimate before
  starting, "≈ 12 min for 4.2 GB").
- **The page** (`review/phone_app.py`, served as `review`: loopback `Host`, JSON-only `POST`): the
  three groups with thumbnails (from the staging copies of the imported files; for cases 1 and 3,
  the PC's file or the quarantine's when there, else a generic tile), counts and sizes per group;
  case 1 and 2 ticked by default, case 3 **never** ticked by default and its warning on each tile;
  "Delete N files (X GB) from the phone" saves `phone-decisions.json` (next to the run's other
  decisions, read back and shown), then the page ends and `mh` goes on.
- **The deletion** (in `mh_phone.ps1.j2`): only the ticked files whose proof passed, the way 0247
  found (no hidden dialog: a way that asks is not used); after each, the phone's folder listed
  again: the file gone is counted, still there is said. A cable pulled: stop, say what was deleted
  and what was not, `mh phone` again starts over from a fresh listing.
- **The journal**: a run of kind `phone` in `/journal` (write-ahead, `pending` then `done`, as
  `clean`): each file deleted from the phone with its name, size, SHA-256 and which case it was —
  `history` shows it; `undo` cannot bring a phone file back (said in the confirm line and in
  `history`), but for cases 1 and 2 the PC copy named in the journal is the file.
- **The final line**, read back from the phone: "Phone freed: 4,980 files deleted (21.3 GB); 3 kept
  (content differs); 31 set aside before, left on the phone" and the one next step.
- Step 19 of `mh-measure.ps1`: the end-to-end run on test files only (the step writes them, as
  0247): import, page, delete, listing again.

## Explicit non-goals

- Deleting anything the page did not show and the person did not tick.
- Folders of the phone outside `DCIM` (WhatsApp, Screenshots): as 0219.
- The phone's own trash or cloud backup (Google Photos): what a deletion over USB does to them is
  said as 0247 measured it, not managed.

## Acceptance

- Unit (`test_phone_free.py`): each case's proof — a file with the same name and size but another
  content is kept; a library file gone since the listing is kept; case 3 with a full or a partial
  digest; the two warnings by quarantine state; the journal entries.
- Integration (`test_phone_review.py`): the page's groups, defaults (case 3 unticked), the saved
  decisions read back, a forged `POST` naming a file outside the plan refused.
- Unit (`test_launcher_phone.py`): the rendered `mh.ps1` deletes only after the decisions file and
  the proof, lists the folder again after each deletion, ASCII.
- Docs both languages: the launcher page, step 3, the safety page (what `undo` cannot do here).
- Windows (maintainer, after the work): the end-to-end run of step 19 on test files.

## Gain (estimated)

Freeing a phone today: copy everything, check by hand, delete in the gallery, hoping nothing was
missed → one command, nothing deleted that the PC does not hold (proved by content) unless the
person ticks it past a warning.

## Decided (2026-10-19)

**Copy, prove, then move** (maintainer): the file is copied from the phone into the staging folder, its SHA-256 compared, and only then deleted from the phone with `MoveHere` into a PC folder (the way 0247 measured with no dialog); the moved copy is then dropped once equal to the staged one. Two reads per file (≈ 6 min for 4.2 GB, estimated at 24 MB/s). Alternative left aside: move first, prove after (one read, but the file leaves the phone before the proof; a cable pulled mid-move not measured).

## Status — PARTIAL (2026-10-19)

### Done
- `mh phone --free` (opt-in; without it the phone is only read, as 0219) and
  `mh phone --only <folder of DCIM>` (keeps every other file out of the import and of the page:
  what makes the Windows measure safe on test files). `cli/templates/mh_phone_free.ps1.j2`,
  values and messages in `services/launcher_phone_free.py`.
- Proof (`services/phone_proof.py`, `phone_holdings.py`, `phone_free.py`): the staged copy's
  SHA-256 against (1) a library file still there (index digest while size+mtime unchanged, else
  read now), (2) the import's own copy (phone size, same SHA-256), (3) the journals (full, else
  partial digest) with the two warnings; else kept with its reason.
- Journal: `Phase.PHONE`, kinds `phone-library`, `phone-imported`, `phone-set-aside`
  (`keeper` = PC copy for 1 and 2); `phone-prove` writes `pending`, `phone-done` writes `done`
  for the files seen gone. `history` shows the run and says undo cannot put files back; `undo`
  refuses a phone run (`undo_guard`), status never proposes it.
- Page (`review/phone_app.py`, `phone_session.py`, `phone_views.py`, `phone_file.py`,
  `templates/phone_review.*`, hidden `phone-review`): three groups, set-aside never ticked and
  its warning per tile, thumbnails of library/import files, every tick saved in
  `/reports/phone-decisions.json` and read back; "Delete" accepted only when the file read back
  holds ticks; `mh` gets the ticked lines read back from the disk; a forged rank refused (422).
- mh.ps1: page → per batch of 100: CopyHere into an empty staging folder → `phone-prove` →
  only proven files `MoveHere` into `<destination>\.mh-moved-<date>` → phone folder listed
  again (up to 10 s) → moved copy Get-FileHash equal → dropped; differing copy kept; still on
  the phone counted; phone unplugged: stop. `phone-done` per batch. Estimate said first (two
  reads at 24 MB/s); final counts read back from the phone.
- Tests: `tests/unit/test_phone_free.py` (17), `tests/integration/test_phone_review.py` (7),
  `tests/unit/test_launcher_phone.py` (+9). Docs en/fr: launcher page, step 3, safety page.
- Step 19p of `mh-measure.ps1`: `mh phone --to <Work> --only mh-measure-free --free` on 3
  synthetic files written to the phone (A, C new; B with a twin of same name/size, other content).

### Not done
- The Windows end-to-end run (maintainer), image built from branch `iterate/2026-10-19-2`:
  ```powershell
  cd C:\temp
  Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/64e5337/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1
  Unblock-File .\mh-measure.ps1
  .\mh-measure.ps1 -Only 19 -Count 1
  ```
  (answer y at 19p, leave the ticks, press Delete: expected A and C deleted, B kept "Not the
  same content", no window, no `.mh-*` folder left, DCIM count unchanged after cleanup).
  **Reason:** needs Windows, Docker Desktop and the phone. Unverified until then: MoveHere of a
  large file, the folder listing after a move, the page served through `docker run -i -p`.
- Thumbnails of set-aside files come from nowhere (generic tile): the quarantine copy is not
  looked up. **Reason:** the journal's remembered set keeps the original host path only.
  → stale: done by 0256, commit 12104de (inbox 2026-10-20).
- Case 2 checks a second independent read of the phone equal to the import copy instead of a
  Pillow/ffprobe decode. **Reason:** byte equality with the phone's own bytes already rules out
  a truncated copy; a decode would only refuse files broken on the phone itself.
  → keep the byte equality, no decode (maintainer, inbox 2026-10-20).
- "Purged on <date>": the purge date is not journaled; the text says "set aside on <date> and
  purged since".
  → stale: done by 0256, commit 12104de (inbox 2026-10-20).
