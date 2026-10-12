# 0103 — PowerShell `mkdir` without `-Force`: a red error the second time

- **Priority**: Low — harmless, but red text scares a beginner
- **Batch**: docs
- **Depends**: —
- **Files**: `README.md`, `README_FR.md`, `documentation/en/clean/04-html-report.md`, `documentation/fr/clean/04-html-report.md`, `documentation/en/clean/07-configuration-file.md`, `documentation/fr/clean/07-configuration-file.md`, `documentation/en/clean/08-clean.md`, `documentation/fr/clean/08-clean.md`, `documentation/en/commands/config.md`, `documentation/fr/commands/config.md`

## Context

UX review of 2026-10-12. Twelve PowerShell blocks start with `mkdir "…"` without `-Force`
(`grep -rn '^mkdir "' README*.md documentation`). The guide creates `reports` in step 4,
`config` in step 7, `journal` and `quarantine` in step 8, and the README's *complete command*
creates all four again: each repeated folder prints a red *An item with the specified name
already exists* error. The quick guides and the tool's own 👉 commands already write
`mkdir -Force`.

## Goal

- `mkdir -Force` in every PowerShell block (the bash ones already use `mkdir -p`).
- A test of `test_documentation.py` that refuses `mkdir "` without `-Force` in a `powershell`
  block.

## Acceptance

- `grep -rn '^mkdir "' README*.md documentation` finds nothing; the new test passes.
