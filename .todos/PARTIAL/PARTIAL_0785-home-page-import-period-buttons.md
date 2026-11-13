# 0785 — Home page: the period buttons before a phone import, and the bursts in the end line

- **Priority**: Low
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/cli/menu_catalog_import.py`, `src/media_hygiene/cli/menu_entry.py`, `src/media_hygiene/review/templates/home_imports.js.j2`, `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/services/import_copies.py`

Filed 2026-11-13 by 0737 and 0738 (what 0478 and 0481 left), after checking each item
against the code: the burst page on the import's bursts (0480), the new event's slideshow
(`slideshow --folder --since`), `copies` before `tags` (0480), the chain followed live and
resumed from a step (0604, `review/import_chain_api.py`) and the toggles saved in
`[imports] then` (0481) are all in. Two items of the maintainer's decisions are not.

## What

- Decided 5 of 0478 / 0476: *Today · This week · This month · All* on the home page before
  *Copy the new photos of the phone* starts (the same buttons as search's dates), handed to
  `mh import --phone --since <period>`. Today the page starts `import --phone` with no period
  (since the last import, `last-import.txt`). Needs a field of fixed choices in `Step.fields`
  (`FieldKind`: none holds choices yet), drawn as buttons on the page and as a numbered
  question by `mh menu`.
- Decided 3 of 0478, its wording: the end line counts the bursts reviewed (« ✨ All done: 42
  imported, 3 copies set aside, 2 bursts reviewed »). Today the copies and the bursts each get
  their own line (`phone-end --copies`, then `clean --decisions import-bursts.json`), the end
  line counts the new files only.

## Explicit NON-goals

- No change to the chain itself (order, file, resume).

## Acceptance

- The period chosen on the page reaches `--since` (test of the command built); `mh menu`
  asks it too; docs en + fr (`commands/import.md`); `docs_screenshots` to run.
- The end line counts the shots of `import-bursts.json` set aside (unit test).

## Status — PARTIAL (2026-11-13)

Done: `FieldKind.CHOICE` (`Field.choices`, `Field.option`: an option added after the
command unless the default is chosen, `cli/menu_words.py`); the phone step asks
*Since the last import · Today · This week · This month · All* as buttons
(`choiceButtons`, `home_draw.js.j2`), handed to `--since` (tests
`tests/unit/test_import_period_bursts.py`); the end line counts the burst series seen
and their shots set aside from `import-bursts.json` (`reviewed_bursts`); docs en + fr.

Left:
- `mh menu` does not ask the period as a numbered question: it runs the import since
  the last one, as before (a choice field has a default, `Step.asks`). The question
  needs a prompt in `mh_menu.ps1.j2` / `mh.sh.j2` (the menu's lines carry no field).
- The copies set aside are not in the end line: `phone-end --copies` runs in its own
  container, its count is not kept for the end (a small file in /reports would do).
- `docs_screenshots` to run (the phone step now opens a form).
