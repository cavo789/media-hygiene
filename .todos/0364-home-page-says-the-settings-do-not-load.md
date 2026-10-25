# 0364 — The home page says when `config.toml` no longer loads

- **Priority**: High
- **Batch**: home
- **Depends**: 0358
- **Files**: `src/media_hygiene/services/fresh_runtime.py`, `src/media_hygiene/review/home_views.py`, `src/media_hygiene/cli/home_state.py`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/review/home_texts.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_fresh_runtime.py`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Context

Review of the feedback of 2026-10-24 (maintainer, 2026-10-25: *a small TODO: say it on the
page*). Since 0358 the home server reads `config.toml` and `/config/people/*.toml` again when they
change; a file that no longer loads keeps the last good settings and says so with
`output.warning` — in the console of the server, which runs in the background since 0355
(`docker run -d`): nobody sees it. The user edits `config.toml`, makes a typo, and the page goes
on with the old settings silently.

## What to do

1. `FreshRuntime` keeps the error of the last failed load (its translated message, the file),
   cleared once a load succeeds.
2. The home page's state carries it (`HomeState.settings_error`, empty when none); the page
   shows one line at the top while it is set: *config.toml cannot be read: <message>. The last
   good settings stay until it is fixed.* with the path as Explorer shows it.
3. The pages served by the home server (search, browse) show the same line in their bar.
4. Tests: a typo → the state carries the message, the old settings stay; fixed → no line; the
   page's template shows the field (text check).
5. Docs en + fr (`commands/home.md`, *Good to know*). `docs_screenshots` to run if a capture
   holds the top of the page (said, not run).

## Acceptance

- A typo in `config.toml` while the home page is open: within a second or two of the next click,
  the line on the page names the file and the error; fixed, the line goes.

## Gain

No silent stale settings after a typo (correctness), said where the user looks.
