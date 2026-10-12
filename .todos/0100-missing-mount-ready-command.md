# 0100 — A missing `/journal` or `/quarantine`: give the ready command, not `--delete`

- **Priority**: Medium — a beginner is pointed to the one irreversible option
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/services/missing_mount.py`, `src/media_hygiene/services/next_command.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_missing_mount.py`

## Context

UX review of 2026-10-12. `clean` without `/quarantine` answers:

```text
❌ clean moves the duplicate copies to /quarantine: mount it.
💡 Add -v "<a folder of yours>:/quarantine" (or --delete to delete them for good at once).
```

and without `/journal`: `💡 Add -v "<a folder of yours>:/journal" to the docker run command.`

- "Mount it", "<a folder of yours>" are left for the beginner to translate into a path, a
  `mkdir`, and the right place in a long command; yet the audit's 👉 line already builds that
  full command (`next_command`: `mkdir -Force …` then the complete `docker run`).
- The alternative offered is `--delete`, the only way besides `purge` to erase content: the
  easiest way out of the error is the riskiest one, against the "nothing is erased" promise
  repeated everywhere else.

## Goal

- The 💡 of a missing `/journal`, `/quarantine` (and the other tool folders: `/reports` for
  `review`, …) prints the same ready-to-paste block as the audit's 👉 line: `mkdir` of
  `$HOME\media-hygiene\…`, then the full command with the mounts of this run plus the missing
  ones; under `mh` (`MEDIA_HYGIENE_LAUNCHER`), "load `mh` again" instead.
- `--delete` is no longer suggested there; it stays documented on the `clean` page.

## Acceptance

- Unit tests: missing `/quarantine` under PowerShell paths and bash paths give a complete
  command; no `--delete` in the message.
