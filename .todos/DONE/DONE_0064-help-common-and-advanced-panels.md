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

## Status — DONE (2026-10-11)

- Rule: a command with more than four options (`audit`, `crosscheck`, `review`, `clean`,
  `classify`, `album`) keeps its options of daily use in Typer's first panel ("Options", with
  `--help`); the others go to "Advanced options" (`options.panel_advanced()`), and the shared
  folder and scan overrides to "Advanced: folders (override folders.* …)" / "Advanced: scan
  (override scan.* …)". Commands with four options or fewer are unchanged.
- Daily options: `clean` `--tier`, `--decisions`, `--yes`; `review` `--near`; `classify`
  `--year`, `--layout`, `--target`; `album` `--category`, `--event`, `--apply`. `audit` and
  `crosscheck` have none (only the overrides). Signatures of `clean` and `review` reordered so
  the panels come Options → Advanced options → Advanced: folders → Advanced: scan.
- `--port` and `--decisions` take an optional panel (`review_options.port(panel)`,
  `clean_options.decisions_option(help, panel)`): advanced in `review`, unchanged in `places`,
  `search`, `review-sort`.
- Purpose-first help: `clean --tier` ("How far to clean … the shrunk copies (sent by WhatsApp or
  e-mail …) … never deleted"), `clean --delete` ("Free the space at once: …"), `clean
  --decisions` ("Apply the choices made in the browser: …", now names the near duplicates),
  `classify --sample` ("Estimate a full run first: …"). French catalogue complete.
- `documentation/{en,fr}/reference-commands.md`: one paragraph explains the panels.
- Not done tonight: the `<!-- capture: help-*.txt -->` blocks still show the old flat lists;
  `docs_screenshots` regenerates them.
- Test: `tests/unit/test_help_panels.py`.
