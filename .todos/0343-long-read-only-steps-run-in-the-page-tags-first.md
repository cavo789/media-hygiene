# 0343 — Long read-only steps run in the page, progress and Stop: `tags` first

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/home_app.py`, `src/media_hygiene/services/home_audit.py`, `src/media_hygiene/services/tags.py`, `src/media_hygiene/services/tag_describe.py`, `src/media_hygiene/console/page_progress.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_home_audit.py`, `documentation/en/commands/tags.md`, `documentation/fr/commands/tags.md`

## Context

Reported by the maintainer (2026-10-24): *tags* started from the home page lands in PowerShell
with `40,099 photos to describe with qwen3.8:27b…, about 21 h 27 min — Describe them now? [y/N]`
(their figures, read from their console). They want long steps run from the page (Ajax), a
progress bar, and a Stop button — for `tags` and every long step.

## What exists

- The audit already runs this way (0211): `POST /api/audit` in the home container, progress
  polled from a page sink (`console/page_progress.py`), one run at a time, a Stop.
- `tags` commits each answer at once: a stop keeps what is described, the next run goes on
  (`services/tag_describe.py` docstring) — so a Stop costs nothing.
- Steps that **write photos** (`clean`, `undo`, `purge`, `sort`) are 0289's design note: not here.

## To do

1. `tags` from the home page runs in the home server like the audit: first the cheap part (words
   from folders, names, dates, places — seconds), then the page asks with the console's figures
   (*40,099 photos, about 21 h; Ollama model …*) and offers: **Describe now**, **Describe for
   1 h / until I stop** (the run stops itself after the chosen time; a setting `[tags]
   max_minutes`? propose it), **Not now**.
2. Progress: photos described / total, rate, time left, the last photo's words; **Stop** ends
   after the photo in flight; reopening the page during a run shows the run.
3. Survey the other long read-only steps (`people` face scan, `meaning`, `inventory`, the
   phone import?) and file one follow-up per step worth it; say which and why in the feedback.
4. Ollama absent / model missing: the page says it in one line, never a traceback.

## Acceptance

- [ ] From the page: `tags` asks with its figures, runs, shows progress, stops on Stop, and the
      next run continues where it stopped (test with a fake Ollama client).
- [ ] The console only prints that the page runs it (the 🔒 / 🤖 lines kept).
- [ ] Docs en + fr; `docs_screenshots` to run.
