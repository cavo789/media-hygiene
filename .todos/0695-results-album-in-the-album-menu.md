# 0695 — *Album of the N found* moves into the 📚 Album ▾ menu of the bar

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/pick_acting.html.j2`, `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/search/templates/search.html.j2`, `.claude/skills/photo-picking-pages/SKILL.md`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0665 (commit f3ab4dd5) grouped the library bar in menus but left *📚 album of the results*
apart: it acts on every file found, not on the picking. Decided: it goes into 📚 Album ▾,
its entry stating the count it acts on ("Album of the 1 234 found"), as the rule *never act on
what is not shown* asks.

## Acceptance

- [ ] The entry in 📚 Album ▾ with the live count; the old place removed
- [ ] The count posted is the one shown (set-aside files left out), test
- [ ] Skill table and docs EN + FR (`commands/library.md`); `docs_screenshots` should run
