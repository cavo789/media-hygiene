# 0249 — Review of 2026-10-19: backups in `mh remembers`, a shell-neutral "window", the *Placed* fold's title

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: 0242, 0243, 0205
- **Files**: `src/media_hygiene/services/launcher_memory.py`, `src/media_hygiene/services/launcher_backups.py`, `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/services/home_audit.py`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/i18n/locales/media_hygiene.pot`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`

## Context

Decisions of the maintainer in the review of `.claude/plans/feedback-2026-10-19-iterate.md`
(2026-10-19). Three small wording changes, filed instead of done at once because a parallel
session held uncommitted changes in the `.po`/`.pot` catalogs (0213). To run **before 0244**, so
its captures show the final wording.

## What to do

1. **`mh remembers` counts the backups** (follows 0205, commit c857503). The closing line of
   `launcher` (`services/launcher_memory.py:remembered`) says `mh remembers: 2 folders, language
   fr, …` and ignores the backups mounted read-only. Say them apart, e.g. `2 folders, 1 backup
   (read-only), language fr, …` (ngettext; no backup → the line as today). Test both.
2. **A shell-neutral window** (follows 0243, commit a178776). "the PowerShell window" is wrong for
   the bash `mh` users. Replace it in every page string with a neutral wording, e.g. "the window
   where mh runs" (`home.html.j2`: runTitle, copyTitle, the Ctrl+C line, the running line;
   `home_audit.py`: the audit failure; `browse.html.j2`: `applying`). Keep "PowerShell" in the
   documentation, which is Windows-first; check the pages quoting these strings
   (`grep -rn "PowerShell window" documentation`) and keep en/fr in sync.
3. **Rename the fold** (follows 0242, commit 9e8ce2d): `places.html.j2` "Folders named after a
   town" → "Folders named after a town, or placed" (its *Placed* sub-list now holds folders placed
   from *Any folder*). Also `noFolder` if it reads wrong next to it.

Then `i18n_update` and translate; tests of the changed modules; say that `docs_screenshots`
should run (0244 does).
