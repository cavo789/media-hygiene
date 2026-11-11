# 0706 — Purge and shrink follow their step with the shared poll of every page

- **Priority**: Low
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/quarantine_purge.js.j2`, `src/media_hygiene/review/templates/shrink.js.j2`, `src/media_hygiene/review/templates/step_chip.html.j2`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0661 (commit 0dc19c87) made one `/api/step` poll per page (chip, follow dialog, *Apply now*);
purge and shrink keep their own and mark the step as theirs. Decided: move them onto the shared
poll (5 s while idle kept).

## Acceptance

- [ ] One poll per page on purge and shrink (test counting the polls in the rendered page)
- [ ] The end announced once; the CI browser walk of the step covers purge
