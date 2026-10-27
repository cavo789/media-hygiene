# 0436 — `mh pull`: the Windows copy, its proof and undo (rest of 0376)

- **Priority**: High
- **Batch**: launcher
- **Depends**: 0376
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, a new `src/media_hygiene/cli/templates/mh_pull.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/pull_plan.py`, a new `pull-step` command in `src/media_hygiene/cli/`, `src/media_hygiene/actions/` (journal `Phase.PULL`), `src/media_hygiene/cli/menu_catalog_*.py`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `tests/measure/mh-measure.ps1`, `documentation/en/commands/`, `documentation/fr/commands/`
- **Needs maintainer**: the crash rehearsal on Windows (a step of `mh-measure.ps1`)

## Why

0376 (PARTIAL, `.todos/PARTIAL/PARTIAL_0376-*.md`, commit d9ee0f0a) built the pure plan only
(`plan_pull`). Everything that writes is left; read its Status for the list.

## Decided (review of 2026-10-27)

- A drive letter of the push target that no longer exists on the PC (disk replaced): `mh pull`
  **refuses** with one line naming the letter and how to map it:
  `mh pull --folder D/Photos=E:\Photos` (maintainer).

## What

The items of 0376's Status: host copy with robocopy (`/XC /XN /XO`, `/COPY:DAT`, never over a
PC file), the `pull-step` container command (target read-only, digests from the index, journal,
SHA-256 proof, `--undo`), the drive-letter refusal and `--folder X/…=Y:\…` mapping above, docs
en+fr ("After a crash"), verb wiring (`COMMANDS_TOO`, catalog, nav), i18n, the bash refusal, the
crash rehearsal step.

## Explicit NON-goals

- Any write on the push target (NAS) during a pull.
