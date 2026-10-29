# 0502 — TV slideshow: the photo blurred behind it instead of black bars

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/slideshow/templates/screen.html.j2`, `src/media_hygiene/slideshow/templates/screen.js.j2`
- **Needs maintainer**: a try on the Samsung TV's own browser (and the Chromecast): smooth or not

## Why

The maintainer, 2026-10-29, photos of the TV: a 4:3 landscape photo leaves a black band left and
right on the 16:9 screen, a portrait one leaves about two thirds of the screen dark. "On pourrait
tenter... Ce serait le même flou qu'une image de chapitre."

## What

- Behind each photo, the same photo filling the screen, blurred and darkened **exactly as the
  event title card does** (`#card img` in `screen.html.j2`: `blur(24px) brightness(0.45)`, 110 %
  to hide the blurred edges): one shared CSS rule for both, not a copy.
- It follows the crossfade (both layers A/B carry their own background), and a video keeps its
  black bars (no blur behind a playing film: the old browser decodes one thing at a time).
- Old browser first: the TV's own browser (a 2012-era Samsung) may stutter on a full-screen CSS
  blur at each change. Measure on the TV: the time between two photos and whether the crossfade
  stays smooth. If it stutters, fall back to a background made on the PC (a small JPEG, already
  blurred with Pillow, `/tv/<key>-behind.jpg`, cached with the previews): no filter in the
  browser at all. Keep a constant (or a `[slideshow]` setting only if TVs differ, see few-settings)
  to switch it off.
- Tests: the page carries the layer, a video slide has none; the PC-made background when chosen.
