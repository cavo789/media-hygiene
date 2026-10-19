# 0225 — Commands named as the user types them: `mh review`, never `media-hygiene review`

- **Priority**: High — the tool gives instructions the user cannot type as written
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/services/next_command.py`, `src/media_hygiene/report/templates/_bursts.html.j2`, `src/media_hygiene/report/templates/index.html.j2`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/review/templates/*.html.j2`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/cli/cmd_*.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/`, `documentation/fr/`

## Problem

Reported by the maintainer (2026-10-17, screenshot of the HTML report, *Rafales* section):
"la choix vous appartient : **'media-hygiene review'** montre les séries une à une…". The user
never types `media-hygiene`: they run `mh review` (the function `mh.ps1` / `mh.sh` writes), or a
full `docker run … cavo789/media-hygiene review` without the launcher. `media-hygiene review`
works only inside the image (`ENTRYPOINT`) or from sources.

Measured (2026-10-17, `grep -n "media-hygiene [a-z]" src/media_hygiene/i18n/locales/media_hygiene.pot`):
**23 msgids** name the tool `media-hygiene <something>`. Of those, these name a *command to
type*, so they are wrong:

- `'media-hygiene undo <run>'`, `'media-hygiene undo {run_id}'` (5 messages: clean, album, the
  "Changed your mind?" lines), `'media-hygiene clean {flag}'`
- `'media-hygiene config'` (3: the console and `config.toml` comments),
  `'media-hygiene history'`, `'media-hygiene crosscheck'` (2), `'media-hygiene audit'`
  (reports index), `'media-hygiene review'` (`_bursts.html.j2`), `'media-hygiene places'`
  (`config.toml` comment)
- `grep -rln "media-hygiene [a-z]" src/media_hygiene --include=*.py --include=*.j2` lists 30
  files; comments and docstrings among them are fine (developer-facing).

The others name the *product* ("Found by media-hygiene only", "media-hygiene report",
"update media-hygiene") and stay.

## Already there

`services/next_command.py`: `LAUNCHER_VARIABLE` (`MEDIA_HYGIENE_LAUNCHER`, set by `mh`) and
`LAUNCHER_FUNCTION = "mh"`; the 👉 *What next* line already says `mh <verb>` when the launcher
ran the tool, the full `docker run` otherwise.

## To do

1. One helper (next to `next_command`) giving the short name of a command as this user types
   it: `mh <verb>` under the launcher; without it, the full `docker run` would be too long
   inside a sentence — decide: `mh <verb>` always (the documented way since 0060) or
   `docker run … <verb>` with a pointer to the 👉 line. Proposal: `mh <verb>` in the sentences,
   the 👉 line keeps the full command when there is no launcher.
2. Pass the command name as a `{command}` placeholder in every message listed above (never
   `mh` hard-coded in a msgid), in the console, the HTML reports (`_bursts`, `index`), the review
   pages and the `config.toml` comments (written once: `mh`, the documented way).
3. A test forbidding `'media-hygiene <verb>'` in the `.pot` msgids (an allowlist for the product
   name), so the mistake does not come back.
4. Documentation EN + FR: grep `media-hygiene <verb>` outside code blocks meant for the image
   itself and the developer page.
5. `i18n_update`, translate; say that `docs_screenshots` should run (console captures change).

## Status — POSTPONED (2026-10-18)

Postponed by the maintainer during `/todo:iterate`: the choice in step 1 (`mh <verb>` always, or
the full `docker run` when the launcher is not used) waits for them. Re-file it flat to run it.
