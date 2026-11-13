# 0738 — What 0481 left: The import chain on the home page (rest of 0480)

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `.todos/DONE/0481-home-page-import-chain.md`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/config/import_settings.py`

Split from section 0481 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0481-home-page-import-chain.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The chain followed live on the home page, a chain stopped halfway resumed from the next

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — DONE (2026-11-13)

Checked against the code: the chain followed live on the home page and resumed from a step
is done by 0604 (`import-chain.json` written by `mh_phone.ps1.j2` before each step,
`GET/POST /api/import-chain`, `home_imports.js.j2` offering the stopped chain from its step;
`tests/unit/test_import_chain.py`). The period buttons are refiled as 0785.
