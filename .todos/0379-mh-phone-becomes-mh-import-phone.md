# 0379 — `mh phone` becomes `mh import --phone`: one verb to bring photos in

- **Priority**: Medium
- **Batch**: import
- **Depends**: 0377, 0378
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/cli/templates/mh_phone_free.ps1.j2`, `src/media_hygiene/services/launcher_phone.py`, `src/media_hygiene/services/launcher_phone_free.py`, `src/media_hygiene/services/launcher_phone_say.py`, `src/media_hygiene/cli/cmd_import.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/review/home_texts.py`, `src/media_hygiene/review/home_texts_run.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/import.md`, `documentation/fr/commands/import.md`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`

## Why

The maintainer, 2026-10-25: "one verb, `mh import`, seems more logical". Every photo tool says
*import* for bringing photos into the library (Lightroom, the Photos app of Windows and of Apple:
*to check* the exact words), and that is what `mh import` (a folder, 0378) and `mh phone` (a phone
over USB, 0219) both do. The photos' own save and restore are `push` / `pull` (0375, 0376), the
index's `backup` / `restore` (0352).

The two keep separate paths where MTP forces it: a phone has no drive letter, Docker cannot see
it, `mh.ps1` copies with `Shell.Application` (`CopyHere`), and matches by name and size (no
content without a copy). Only the verb and the rule of reasons (0377) are shared.

## What to do

1. `mh import --phone [--to <folder>]` and `mh import --phone --free`: what `mh phone` and
   `mh phone --free` do today; a host command of `mh.ps1` for `--phone` only (`mh import` of a
   folder stays a container command). The bash `mh` refuses `--phone` as it refuses `mh phone`.
2. `mh phone`: removed (the maintainer is the only user; no alias), or one line pointing to
   `mh import --phone` for a version (*to decide* at implementation: say which in the report).
3. Destination: `From phone` (or the phone's name as Windows shows it, *to design*), consistent
   with 0378's `From <source>`; today's phone destination kept if the user set one (`--to`).
4. The home page and the phone page (`home_texts*`, the run texts) say `import --phone`; the
   menu: one "Import" stage with two actions (a folder, a phone).
5. Docs en + fr: the phone section moves into `commands/import.md` ("From a phone"), the
   launcher page's table updated, `reference-commands.md`, mkdocs `nav`, `COMMANDS_TOO`;
   `i18n_update` + French; `docs_screenshots` to run (said, not run).
6. 0337 (import then free the phone in one go) and the open `phone` batch (0313, 0322, 0330,
   0336, 0338) keep their content: their texts and files say `mh import --phone` once this lands
   (update their headers when they are run).

## Acceptance

- `mh import --phone` then `mh import --phone --free` on the maintainer's phone: the same plan,
  copies and proofs as `mh phone` before (`Needs maintainer` at run time: a phone plugged in).
- `grep -rn "mh phone" src documentation` finds nothing (or only the pointer line of point 2).

## Gain

One verb to learn for "bring photos in", whatever the source (*estimated*: one verb fewer in
`mh --help`, the menu's import stage in one place). No speed change.
