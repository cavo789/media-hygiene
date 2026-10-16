# 0191 — `[clean] quarantine_headroom_gb`: the space clean keeps free on the quarantine's drive

- **Priority**: Low
- **Batch**: quarantine-drives
- **Depends**: —
- **Files**: `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/services/quarantine_space.py`, `src/media_hygiene/cli/clean_space.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/clean/07-configuration-file.md`, `documentation/fr/clean/07-configuration-file.md`, `tests/unit/test_clean_space.py`

## Why

Decided at the review of the 2026-10-16 run (question 8, about 0182): `clean` refuses a move
that would leave less than 1 GiB free on the quarantine's drive (`QUARANTINE_HEADROOM` in
`services/quarantine_space.py`, a constant). A small `C:` may want 0, a large one more.

## What

- `CleanSettings.quarantine_headroom_gb: float = 1` (`ge=0`), in `[clean]`, with its line and
  comment in the default `config.toml` template; env `MEDIA_HYGIENE_CLEAN__QUARANTINE_HEADROOM_GB`.
- `quarantine_space.py` reads it instead of the constant (passed in, not read globally: the
  function keeps ≤ 3 parameters, a frozen object otherwise); `clean_space.py` shows the value set.
- 0 means "no margin": the refusal only when the files do not fit at all.
- Tests: default 1 GiB unchanged; 0 lets a move that fits exactly; a larger value refuses earlier.
- Docs EN/FR: the `[clean]` table of the configuration reference.
