# 0560 — TV slideshow: cross-fade and a slow Ken Burns, switched on/off from the phone

- **Priority**: Medium
- **Batch**: tv-slideshow
- **Depends**: 0502
- **Files**: `src/media_hygiene/slideshow/templates/screen.html.j2`, `src/media_hygiene/slideshow/templates/screen.js.j2`, `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`, `src/media_hygiene/slideshow/show.py`, `src/media_hygiene/slideshow/routes.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`
- **Needs maintainer**: watch it on the family TV (smoothness of its browser)

## Reported (maintainer, 2026-11-01)

A show without any animation is dull on a big screen: each photo replaces the last one
abruptly (checked: `screen.*.j2` has no transition today). Wanted: the Ken Burns effect,
switched on/off from the phone, as the music will be (0544).

## What

- **Cross-fade** (~1 s, estimated comfortable value) between two photos, always on: the
  next one fades in while the current one fades out. Videos fade in and out too.
- **Ken Burns**: during a photo's time, a very slow zoom (~5 %, estimated) and pan,
  direction varied from one photo to the next. Not on videos while they play. With 0502,
  only the photo moves, the blurred background stays still. Avoid cutting a face when the
  index has face boxes (zoom towards them, else towards the centre).
- **No flashy effects** (explosion, cube, wipes): decided with the maintainer.
- **Phone**: a "🎞 Animation" on/off button on the remote, next to the show's other
  controls (and to 🎵 of 0544). Held by the show (`show.py`, raises `version`) so the TV
  follows at once; default on. Not a `config.toml` setting (memory "few settings").
- **TV browser**: CSS `opacity` and `transform` only (GPU-friendly), the next photo
  preloaded and decoded (`img.decode()`) before the fade starts, otherwise it stutters.
  `prefers-reduced-motion`: Ken Burns off.
- Tests: the toggle round-trip phone → show → TV page; docs in both languages; say that
  `docs_screenshots` should run.
