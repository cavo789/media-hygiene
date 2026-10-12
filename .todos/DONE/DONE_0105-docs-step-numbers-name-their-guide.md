# 0105 — "Step 7" means two things: name the guide in every cross-guide step link

- **Priority**: Low — a wrong turn for readers of the sort guide
- **Batch**: docs
- **Depends**: —
- **Files**: `documentation/en/start/01-first-audit.md`, `documentation/fr/start/01-first-audit.md`, `documentation/en/sort/*.md`, `documentation/fr/sort/*.md`, `documentation/en/reference-mount-points.md`, `documentation/fr/reference-mount-points.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`

## Context

UX review of 2026-10-12. Both guides number their steps from 4: *step 7* is *The configuration
file* in the clean guide and *Sort* in the sort guide. Some links say which one (*step 7 of the
clean guide*), others do not:

- `sort/04-classify.md`: "in the `[classify]` section of `config.toml` ([step 7](../clean/07-configuration-file.md))" — a reader of the sort guide expects *Sort*.
- `start/01-first-audit.md`: "[Step 7](../clean/07-configuration-file.md) makes it permanent"
  (the `--locale` tip), read by everyone, before choosing a guide.
- The *Guide* columns of `reference-mount-points.md` and `reference-commands.md` give bare
  numbers (`[7]`, `[8]`) for the clean guide and *Sorting, 4* for the other.

## Goal

- Every link from a page to a step of **another** guide names it: *clean, step 7* /
  *nettoyage, étape 7*; better, by its title: *[the configuration file](…)*.
- The reference tables write *Clean, 7* the way they already write *Sorting, 4*.

## Acceptance

- `grep -rn "\[step [0-9]*\](\.\./clean" documentation/en/sort` (and the French equivalent) finds
  nothing.
