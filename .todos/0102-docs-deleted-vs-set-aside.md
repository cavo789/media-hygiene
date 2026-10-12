# 0102 — Step 1: the table says "can be deleted", the screen says "set aside"

- **Priority**: Low — one wrong word, but on the promise of safety
- **Batch**: docs
- **Depends**: —
- **Files**: `documentation/en/start/01-first-audit.md`, `documentation/fr/start/01-first-audit.md`

## Context

UX review of 2026-10-12. The capture of step 1 shows the line *Extra copies that can be set
aside* (*Copies en trop, à mettre de côté*), but the table explaining it right below names it
*Extra copies that can be deleted* — "The files a clean would delete" (*supprimables*, *qu'un
nettoyage supprimerait*). A beginner reads "delete" on the very first page, where the whole tool
promises that `clean` only moves files to the quarantine.

## Goal

- Use the wording of the screen: *Extra copies that can be set aside* — "The files a clean would
  move to the quarantine"; French: *Copies en trop, à mettre de côté* — « les fichiers qu'un
  nettoyage mettrait en quarantaine ».
- Grep the other pages for the same drift (*deleted*, *supprim*) next to `clean` without
  `--delete`.

## Acceptance

- The table row matches the captured line, in both languages.
