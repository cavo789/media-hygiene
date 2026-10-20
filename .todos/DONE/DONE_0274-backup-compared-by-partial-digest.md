# 0274 — A backup compared by size and partial digest, never read whole (a NAS in hours → minutes)

- **Priority**: High
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/services/audit_analysis.py`, `src/media_hygiene/plan/backups.py`, `src/media_hygiene/scan/exact.py`, `src/media_hygiene/services/import_plan.py`, `tests/unit/test_backups.py`, `tests/integration/test_backup_audit.py`, `tests/integration/test_import_run.py`, `documentation/en/commands/import.md`, `documentation/fr/commands/import.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`

Follows 0245 (PARTIAL). Decided by the maintainer on 2026-10-20: a TODO, built later.

## Measured (2026-10-20, step 21h of mh-measure.ps1, the maintainer's Synology DS216j)

- The NAS as an `mh` backup over SMB3 (Docker CIFS volume): reads at **15 MB/s** through
  Docker Desktop (Windows itself: 105 MB/s).
- `mh audit` with the NAS and a test library of **one photo**: stopped by Ctrl+C after
  **8,164.5 s (2 h 16)**, not finished. CPU 2.6 %: waiting for the network.

Why: the audit puts the backup's files through the exact pipeline (`exact.find([*healthy,
*backup])`, `services/audit_analysis.py`): every file sharing a size with another (the
NAS's own copies: `2007` / `2007b`, …) gets its partial digest, then is **read whole** when
the partials match. With the real library (almost the NAS itself), nearly every NAS file has
a twin of its size on the PC and would be read whole to be proven: estimated **5 h 30 for
300 GB** at 15 MB/s (estimated from the measured rate), at each first audit.

## To do

A backup is only compared, never cleaned: "a copy is in the library" needs no byte-for-byte
proof. Its files are matched with the library by **size, then partial digest** (first and last
64 KiB: `scan.hashing.partial_digest`, as the gone files are, 0224), never read whole:

1. `analyse`: the exact pipeline on the library alone (its groups still proven in full for
   `clean`); the backup's files of a size some library file has get their partial digest (the
   library files of those sizes too, from the index, else read); a backup file whose
   (size, partial) a library file shares is covered; the others are `only`.
2. The backup's own twins (identical files inside the NAS): matched by (size, partial) too,
   for `import`'s "copied once" (`services/import_plan._unique`), which reads `full_digest`
   today.
3. `missing` (the library files a backup lacks) by the same key.
4. `import` still proves each copy in full (`actions/copy_in`: the source hashed as it is
   read, the copy read back): only the files really copied are read whole.
5. The set-aside and deletion matching (`services/backup_dealt.py`) already work by partial
   digest when the full one is unknown: check they no longer trigger full reads of the
   backup.
6. Tests: a backup file whose start and end match a library file but whose middle differs is
   counted covered (the documented trade-off: it stays on the NAS, nothing is lost); no backup
   file is read whole by an audit (a spy on `full_digest`); the counts unchanged on the demo
   tree.
7. Docs en/fr: the speed paragraph of `import.md` and step 3 (the first audit of a NAS
   reads 128 KiB per file).

## Settings?

None: the backup is never changed, the trade-off is safe; a setting for the full proof could
come if a user asks.

## Gain

Estimated from the measures: 128 KiB per file instead of the whole file. 300 GB of photos of
about 5 MB (60,000 files) → about 7.5 GB read at 15 MB/s, **about 8 min instead of 5 h 30**
for a first audit with the NAS; the next ones read only what changed (index).
