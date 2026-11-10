# 0690 — Silent corruption: files re-read from time to time, a damaged one found and restored from its copy

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/index/`, `src/media_hygiene/scan/exact.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/services/upkeep.py`, `src/media_hygiene/services/push_proof.py`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The index trusts a file whose path, size and modification time did not change: its digest
is not computed again (that is what makes audits incremental). A disk that silently damages
a file (bit rot, a failing sector, a bad cable to a USB disk) changes neither size nor
date: the audit keeps saying *fine*, and the next `mh push` sees nothing to copy — or, if
the date moved, **copies the damaged file over nothing but still keeps the old one in
`.removed` for 90 days only**. `push` compares size, date and the first and last 64 KB
(`commands/push.md`). No command re-reads old files (`grep` for scrub / bit rot over `src`,
the docs and the backlog, 2026-11-10: nothing). Family archives are exactly the files read
once in ten years.

## Proposal

- **A slow re-read** (`mh upkeep`'s routine, and offered on the safety card): each run
  re-hashes the files whose digest is oldest — a budget in minutes or GB per run, so the
  whole library is covered about once a year (estimate the pace from the maintainer's
  measured read speed and library size). The index keeps `verified_at` per file.
- A digest that changed while size and date did not is **never** treated as an edit: the
  file is listed as *damaged since <date>*, with where a good copy is — a duplicate, the
  quarantine, the NAS (`push`'s listing: same size, same ends → then the full digest of the
  NAS copy, read by Windows).
- *Restore this one* from the good copy, journaled, the damaged file kept in the quarantine.
- `push` never replaces a NAS copy by a file known as damaged (it already refuses a file
  the audit found *broken*: extend the rule).
- The same re-read, sampled, for the NAS copies (`push --verify 2 %`).

Cache rule of the workflow: list what else changes a digest without size or date (a tool
that rewrites EXIF and restores the mtime, `touch -r`) — these are edits, said as *changed
or damaged — look*; one test per event.

## Acceptance

- [ ] A test flipping one byte of a demo photo keeping its mtime: found by the re-read,
      listed, restored from its copy, disk identical to before the flip
- [ ] The pace measured: GB re-read per run within the budget; said whether the budget
      should be a setting (proposed: yes — it depends on the library and the disk)
- [ ] Docs EN + FR

## Where the user gains

Before: a damaged photo is found the day someone opens it, possibly after its good copy
left the NAS. After: found within about a year at worst (estimated), while a good copy
still exists, and repaired in one click.
