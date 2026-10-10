# 0059 — What next prints the full command, ready to paste

- **Priority**: High — the step every user takes after the first audit
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/cli/flows.py`, `src/media_hygiene/console/output.py`, `src/media_hygiene/paths/host_sources.py`, `src/media_hygiene/services/tool_mounts.py`, `documentation/en/`, `documentation/fr/`

## Context

Filed from the 2026-10-10 usability review (pedagogy axis). The audit ends with
`👉 What next: run 'clean' (same -v options, without :ro) …`: the user has to rebuild an
eight-line `docker run` by hand, which is where non-readers get lost. The tool already
builds a full, correct `docker run` from the mount table for the Czkawka second opinion
(`services/tool_mounts.py`), so it knows every host path and mount.

## Proposal

- Build the real `docker run` of the next verb from the mount table:
  - `clean`, `purge`, `undo`: drop `:ro` on `/data/*`, add `/journal` and `/quarantine`,
    keep `/cache`, `/reports`, `/config`, `-e TZ` when set.
  - `review`, `review-sort`, `places`: add `-p 127.0.0.1:PORT:PORT`.
  - A mount the next verb needs but the current run lacks (`/journal`, `/quarantine`): a
    default host path (`$HOME\media-hygiene\journal`) and one line saying so.
- Print it with `Output.command()` under the 👉 line, PowerShell syntax (backtick
  continuations) by default; the host shell is guessed from the mount table (`C:\` paths →
  PowerShell, else bash).
- Every `next_step()` that names a verb uses it (audit → clean, clean → undo/purge,
  review stopped → clean --decisions, classify → sort …).

## Acceptance

- After `demo`, the command printed by the audit, pasted as is, runs `clean`.
- Unit tests: the command built for each verb (ro removed, mounts added, port published).
- Console captures regenerated (`docs_screenshots`, en and fr); `i18n_update` done.
