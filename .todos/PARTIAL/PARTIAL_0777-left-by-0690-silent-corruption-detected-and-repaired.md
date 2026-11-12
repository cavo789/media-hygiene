# 0777 — What 0690 left: Silent corruption: files re-read from time to time, a damaged one found and restored from its copy

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0690-silent-corruption-detected-and-repaired.md`, `src/media_hygiene/scan/exact.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/services/upkeep.py`, `src/media_hygiene/services/push_proof.py`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`

Split from section 0690 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0690-silent-corruption-detected-and-repaired.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Web side: the safety card offer and a *Restore this one* page (the console path shows the
- A test flipping one byte of a demo photo keeping its mtime: found by the re-read,
- Docs EN + FR

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-12)

### Done
- Checked against the code, already done by 0690: the test flipping one byte keeping the mtime
  (`tests/integration/test_reread_repair.py::test_a_flipped_byte_is_found_listed_restored_and_undone`:
  found by the re-read, listed with its good copy, restored byte-identical with its date, undone),
  and the docs EN + FR (`reference-safety.md` *A file damaged by the disk*, `audit.md`, `clean.md`,
  `upkeep.md`, `push.md`).

### Not done
- Web side: the safety card's offer and a *Restore this one* page → filed as 0783.
  **Reason:** a page of photos shown as tiles (skill `photo-picking-pages`), held back with every
  tile page of the run of 2026-11-12 for PR #80; the card's offer alone would be a fast path
  without its visual twin (*seeing first*, 0524), so both wait together.
