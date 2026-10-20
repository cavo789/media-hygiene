# 0260 — The port of the pages (8088) as a `config.toml` setting

- **Priority**: Low
- **Batch**: launcher
- **Depends**: 0259
- **Files**: `src/media_hygiene/cli/review_options.py`, `src/media_hygiene/config/`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/cli/cmd_launcher_parts.py`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_guards.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `documentation/en/`, `documentation/fr/`

Follows 0253 (commit 12104de), decided in the review of feedback 2026-10-19-3 (2026-10-20):
someone whose port 8088 is held by a program they cannot close (a company tool, another server)
has no way out today. 0253 names that program, then says "mh always uses this port".

## Today

`PAGE_PORT = 8088` (`cli/review_options.py`) is the default of every page command's `--port`
(`review`, `review-sort`, `people`, `search`, `places`, `home`…), of the `NextVerb` suggestions
(`cmd_tags.py`, `audit_people.py`, `audit_actions.py`) and of the `-p 127.0.0.1:<port>:<port>`
written by `launcher` into `mh.ps1` / `mh.sh` (`script.commands.port`).

## To do

- A setting (proposed `[review] port`, default 8088; check the section name against the
  existing ones), read by every page command as its `--port` default, and by the suggestions.
- `launcher` writes the configured port into `-p` of `mh.ps1` / `mh.sh`; since `mh update`
  regenerates the scripts, a changed setting needs `mh update` — or `mh` reads it at each run?
  Decide while implementing: the scripts read `config.toml` nowhere today (keep it so; then say
  "type `mh update` after changing it" in the setting's comment).
- 0253's line: in place of "mh always uses this port", the setting to change (one line, the key
  and `mh update`).
- `config.toml.j2` comment, `i18n_update` + French, docs en + fr (the setting in the reference
  page of `config.toml`, the port line in `reference-troubleshooting.md`).
- Tests: the setting reaches each page's default, the rendered `-p` of both scripts, the 0253
  line; the port inside the container and on the host stay the same number (`reviewing.py`
  relies on it).

## Gain

Estimated: a user stuck on a held 8088 goes from no way out to one setting + `mh update`;
nobody else sees a change.
