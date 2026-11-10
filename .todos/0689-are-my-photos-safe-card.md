# 0689 — *Are my photos safe?* — one card: copies, last push, last backup, journal, quarantine

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/services/status.py`, `src/media_hygiene/services/status_parts.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/services/push_journal.py`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The safety nets exist but each lives in its own command: `push` (NAS copy), `backup` (the
index and settings), the journal, the quarantine, `--backup` folders compared. Nothing
answers in one look the question the maintainer asks in this review: "did we think of the
backups?" — for *his* library, today. A user can run `mh` for a year without ever pushing,
and nothing says it.

## Proposal

A card on the home page (and `mh status`, the same lines), read from disk each time, green
/ amber / red per line, each with its one-click fix:

| Line | Green when |
|---|---|
| A second copy of the photos | a push target is set and the last complete push is < 30 days old; N files are newer than it |
| The copy is off this PC | the target is a NAS / another disk (not `C:`) |
| The tool's memory | last `mh backup` < 30 days, copied off the PC |
| The way back | every run of the history still has its journal; the quarantines are mounted |
| Waiting in the quarantine | X GB, oldest N days; how many are only copies (see the quarantine TODO) |
| Never tested | the last time a restore was **tried**: *Try now* restores 20 random photos from the NAS to a temp folder and compares them (SHA-256), then removes them |

The last line is the difference between a backup and a hope: a restore drill, harmless,
one click (Windows side: `mh pull` to a temp folder — depends on what 0436 leaves).

The 30-day figures: constants (say in the report whether they should be settings —
proposed no).

## Acceptance

- [ ] The card with real values on the demo tree in each state (no target, old push,
      everything green), tests over `home_states`
- [ ] The drill run on the maintainer's NAS once (a step of `mh-measure.ps1`), its line
      turning green, read back
- [ ] Docs EN + FR; `docs_screenshots` should run

## Where the user gains

Before: the answer to "am I backed up?" takes 4 commands and some reading. After: one card,
and a backup that was actually tried.
