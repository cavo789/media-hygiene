# 0081 — An unknown key in config.toml is explained, not "Extra inputs are not permitted"

- **Priority**: Medium — any user with a typo, or a config.toml written by a newer version
- **Batch**: config
- **Depends**: —
- **Files**: `src/media_hygiene/config/loader.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_config.py`

## Context

`load_settings` turns every pydantic error into `Invalid configuration (<loc>: <msg>)` with the
raw English pydantic message. For a key the version does not know, the user reads:

```
❌ Configuration invalide (general.timezone: Extra inputs are not permitted).
```

Seen when a config.toml written following the advice of a newer build (`timezone` in
`[general]`) was read by the published v0.3.0. The tip, "Run 'media-hygiene config'", is not a
command a Docker user can type either.

## What to do

- For `error["type"] == "extra_forbidden"`: a translated message naming the key, its section and
  the file on the host (`runtime.mapper` is not available in the loader: pass the host path in, or
  say `config.toml`), e.g. "`timezone` in [general] of config.toml is unknown to this version
  (0.3.0): a typo, or a setting of a newer version? Remove the line, or update the image with
  `docker pull cavo789/media-hygiene`." Suggest the closest known key (`difflib.get_close_matches`)
  when there is one.
- Other pydantic errors: keep the key, and translate the common types (`int_parsing`,
  `bool_parsing`, `enum`, `greater_than_equal`) rather than showing pydantic's English.
- Same treatment for an unknown `MEDIA_HYGIENE_<SECTION>__<KEY>` variable (say "variable", not
  "file").
- Tip: "Run 'config' with the same docker run to see every setting and where it comes from."

## Acceptance

- Unit tests: an unknown key, a near-miss typo (`timezon`), a bad type; output in French has no
  English pydantic text; no traceback.
