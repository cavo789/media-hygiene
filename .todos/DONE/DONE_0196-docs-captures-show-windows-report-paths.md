# 0196 — Docs captures: the reports' paths as a Windows reader sees them

- **Priority**: Low
- **Batch**: docs
- **Depends**: —
- **Files**: `tests/support/docs/host_paths.py`, `tests/support/docs/container.py`, `tests/unit/test_docs_host_paths.py`

## Why

Asked by the maintainer (2026-10-16), after 0195: the captures of the Windows-first pages
print `✅ HTML report: /reports/20261016-192337-audit/report.html`, the container's path. On
Windows, `mh` mounts `$HOME\media-hygiene\reports` and the tool prints that host path. The
docs generator keeps the reports in a Docker volume (never a folder of the maintainer's own
`C:`), so the tool cannot know a Windows path there.

## What

- `tests/support/docs/host_paths.py`: `as_on_windows(screen)` writes every `/reports/…` path
  of a capture as `C:\Users\you\media-hygiene\reports\…` (`\` separators). Not a `-v …:/reports`
  option, not prose. A line made longer than the terminal (80 columns) puts the path on the next
  line, as Rich does.
- `container.py`: `run` and `run_confirmed` pass their tidied screen through it.
- Unit tests on the rewrite: a report line, a long one wrapped, a `-v` left alone.
- Not rewritten: the tool's own sentences for an unknown host folder ("the folder mounted on
  /reports"); the real Windows output says another sentence there (to check per message),
  which the generator cannot render without guessing.

## Acceptance

- Unit tests green; after `docs_screenshots`, the report lines of the guides read
  `C:\Users\you\media-hygiene\reports\…`.
