# 0039 — The decisions file and Windows encodings: accept a BOM, explain PowerShell 5.1's display

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: `src/media_hygiene/report/decisions.py`, `tests/unit/test_review.py`, `src/media_hygiene/config/layers.py`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `documentation/en/clean/10-review-bursts.md`, `documentation/fr/clean/10-review-bursts.md`

## Context

User feedback on 0.2.0 (2026-09-29): `decisions.json` shows `C:\Photos\2005\Décembre 2005 -
Manon & Chloé\…` in Notepad, but `type .\decisions.json` in PowerShell shows `DÃ©cembre` and
`ChloÃ©`. The file is right (UTF-8, no BOM, as `write_decisions` writes it): Windows PowerShell
5.1 reads a file without BOM in the ANSI code page (Windows-1252); PowerShell 7 reads UTF-8.

Harmless to look at, but the other direction is a real bug: `read_decisions` refuses a file that
starts with a UTF-8 BOM (checked: pydantic "Invalid JSON: expected value at line 1 column 1").
A user who edits the file and saves it as "UTF-8 with BOM" in Notepad, or rewrites it with
PowerShell 5.1 (`Set-Content -Encoding UTF8` always adds a BOM; `>` / `Out-File` write UTF-16),
gets "is not a valid decisions file" from `clean --decisions` and from `review` resuming.

## Proposal

- **Read**: decode by BOM before validating — UTF-8 with BOM (`utf-8-sig`) and UTF-16 with a BOM
  (what PowerShell 5.1 redirection writes); no BOM stays UTF-8. Same tolerance wherever the tool
  reads a file the user may have edited (only the decisions file today; `config.toml` goes
  through `tomllib` in `config/layers.py` — check it too).
- **Write**: keep UTF-8 **without** BOM (JSON, RFC 8259 §8.1: `jq`, Python's `json` and browsers
  expect none). `plan.csv` keeps its BOM: Excel needs it.
- **Docs**: a troubleshooting entry "Accents look wrong with `type` in PowerShell": the file is
  fine; `Get-Content -Encoding UTF8 .\decisions.json`, PowerShell 7, or Notepad show it right.
  Link it from step 10 where the file is shown.

## Acceptance

- [ ] A decisions file with a UTF-8 BOM, and one in UTF-16 LE with BOM, load in `clean
      --decisions` and in `review` (unit tests, accented host paths).
- [ ] `review` still writes UTF-8 without BOM (test on the first bytes).
- [ ] Troubleshooting entry in EN + FR, linked from step 10 (`test_documentation.py` passes).
