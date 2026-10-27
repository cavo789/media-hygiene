# 0337 — Import then free the phone in one go: the import's copy is the proof, folders kept on the phone

- **Priority**: Medium
- **Batch**: phone
- **Depends**: 0336
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/cli/templates/mh_phone_free.ps1.j2`, `src/media_hygiene/services/launcher_phone.py`, `src/media_hygiene/services/launcher_phone_free.py`, `src/media_hygiene/services/phone_plan.py`, `src/media_hygiene/services/phone_proof.py`, `src/media_hygiene/services/phone_review.py`, `src/media_hygiene/review/phone_session.py`, `src/media_hygiene/config/`, `tests/measure/mh-measure.ps1`, `.claude/plans/` (design note)

## Why

The maintainer, 2026-10-23, after freeing their phone (about 4 min for the files ticked, *the
console's estimate*): `mh phone --free` reads every ticked file **twice** over USB — a copy into
`.mh-phone-<date>` to prove its content (SHA-256) against the PC, then `MoveHere` to take it off
the phone (a delete verb asks in a window behind the console, measured), that moved copy
compared then dropped. Over MTP the phone gives only a name, a size and a date, never a hash:
reading a file means copying it.

Their idea: "when I import from the phone, the file was just copied: we know it is the same, so
it could be deleted then, without this second check. But not everything: some photos must stay
on the phone — show the `--free` page right after the import, where I say which folders stay on
the phone and which photos really leave it."

## What — a design note first, then follow-up TODOs

The work is to think it through (the maintainer: "it deserves thinking"): write
`.claude/plans/0337-import-then-free.md`, then file the implementation TODOs once the
maintainer has read it. The note answers, with figures marked measured or estimated:

1. **The import's copy as proof.** During `mh phone`, each new file is read once into the
   library (staged `.mh-phone-<date>`, then moved to its place). Its digest at that moment is the
   phone file's content: keep it (path on the phone, size, date, digest) for the `--free` that
   follows, and skip the proof's copy for those files when the phone still lists them with the
   same size and date. What it does not cover: files **already** in the library or imported by an
   earlier run (not read this time) — they still need today's proof. Say the share of each on a
   real import (measured with `mh-measure.ps1`).
2. **The second read.** `MoveHere` transfers the file again. Measure on the maintainer's phone
   whether a delete without a dialog exists over MTP from PowerShell 5.1 (`InvokeVerb`,
   `Shell.Application` flags, `IFileOperation` without run-time compile — Avast, memory), and
   what one read instead of two gains (estimated: about half the time). If none: keep the move,
   compare it to the import's digest (one read, the move) — the proof's copy is still saved.
3. **One session**: `mh phone` ends on the free page (the same page, 0312/0314 and its frame,
   0333) instead of a second command; the import's console summary first, then the page.
4. **What stays on the phone.** Folders the user keeps on the phone (`WhatsApp`, a folder they
   made): remembered across sessions, keyed by the phone's name and the folder below `DCIM`
   (`[phone] keep_folders`? or per phone in `config.toml` — a setting the maintainer reviews),
   never ticked by default, shown folded with "kept on the phone"; what happens when a folder is
   renamed on the phone (offered again, unticked — workflow rule on path-keyed data).
5. **Safety unchanged**: nothing leaves the phone before the user presses Delete on the page; a
   file whose size or date changed since the import is proven again; the journal as today.

## Measure (maintainer, Windows)

A step in `tests/measure/mh-measure.ps1`: on the phone plugged in, a delete without a dialog
tried on one test file copied there for it (never a photo), and the time of `CopyHere` vs
`MoveHere` for 20 files.

## Explicit NON-goals

- *Apply now* rounds on the free page (0315).
- Folders outside `DCIM` (0322).

## Status — PARTIAL (2026-10-26)

Done: the design note `.claude/plans/0337-import-then-free.md` (private) answers points 1–5
with figures marked measured (0219, 0247/0248) or estimated: no dialog-free delete over MTP
(InvokeVerb/InvokeVerbEx ask, measured 0248; IFileOperation needs Add-Type, refused for Avast),
so MoveHere stays; files imported in the same session skip the proof's CopyHere when the phone
lists the same size and date and the library copy re-hashes equal and passes the image check;
the moved copy is compared to the import's digest, a differing one kept in the quarantine
(`--free` reads per file 2 → 1, about half its time, estimated). Step 19r of `mh-measure.ps1`:
20 synthetic test files (4 MB random bytes) written to `DCIM\mh-measure-speed`, CopyHere vs
MoveHere back, SHA-256 against the originals, DCIM counted before and after.

Left (maintainer): read the note, answer its questions ("move, then compare" accepted?
`keep_folders` per phone or one list?), run `.\mh-measure.ps1 -Only 19 -Count 1` with `y` at
19r; then file the four implementation TODOs the note lists. No code deletes anything new yet.
