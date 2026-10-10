# 0064 — Help in two panels: Common and Advanced options

- **Priority**: Low
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/cli/options.py`, `src/media_hygiene/cli/clean_options.py`, `src/media_hygiene/cli/scan_options.py`, `src/media_hygiene/cli/cmd_classify.py`, `src/media_hygiene/cli/cmd_album.py`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`

## Context

Filed from the 2026-10-10 usability review. `clean` and `classify` have nine options each,
listed flat. Some help texts say what an option does, not what it is for: `--tier near`
reads as jargon.

## Proposal

- Typer `rich_help_panel`: the 2–3 options of daily use first ("Common"), the rest under
  "Advanced". Same split for every command with more than four options.
- Help texts lead with the purpose: `--tier near` → "also move the shrunk copies
  (WhatsApp, e-mail) and re-encoded videos — to the quarantine, never deleted".

## Acceptance

- Help blocks of the docs regenerated; French catalogue complete.
