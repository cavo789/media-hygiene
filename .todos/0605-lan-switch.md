# 0605 — Local network sharing as a switch on the page

- **Priority**: Low
- **Batch**: privacy
- **Depends**: 0536 (PARTIAL)
- **Files**: `src/media_hygiene/config/`, the phone/share page

## Why (review of feedback-2026-11-03-iterate (2026-11-05))

`[review] lan` and `lan_phone_originals` are only in config.toml. Decided: a switch (0535 pattern: saved with tomlkit, read back and shown), each choice saying its consequence, and that it applies at the next start.
