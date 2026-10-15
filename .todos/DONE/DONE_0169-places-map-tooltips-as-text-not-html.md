# 0169 — places map: tooltips set as text, not HTML (XSS safe without the name validator)

- **Priority**: Low — defense in depth, nothing exploitable today
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/templates/places.html.j2`, `tests/unit/test_places_page.py` (new: no test renders the page yet)

## Why

A whole-codebase security review (2026-10-15, `/security-review` widened to `src/`) found no
vulnerability, but one sink that is safe only by accident of another module:

- `places.html.j2` (`draw()`) calls Leaflet's `circle.bindTooltip(string)` twice: for each
  cluster (`fill(T.inPlace, { place })`) and for each saved place (`place.name`, permanent label).
  Leaflet puts a string tooltip content in the DOM with `innerHTML` (to check against the vendored
  Leaflet version in `places/static/` before relying on it).
- The page's CSP (`places/app.py:43`) allows `script-src 'self' 'unsafe-inline'`, so an inline
  event handler in an injected tag (`<img src=x onerror=…>`) would run.
- The names come from `config.toml` `[[classify.places]]`, which `places` itself writes, partly
  from Nominatim answers (`POST /api/osm` → `found.name`), i.e. third-party text. Today every name
  goes through `PersonalPlace._folder_name` → `check_layout`, whose `_FORBIDDEN` pattern
  (`classify/layout.py:22`) rejects `<` and `>`: no tag can get in.

If that validator is ever loosened (it exists for folder names, not for HTML), a place name from
OpenStreetMap could run a script in the map page, which can read the GPS clusters of the
collection and send them out by navigation — breaking "no position ever leaves the machine".

## What to do

- Build the tooltip content as a DOM node: `const label = document.createElement("span");
  label.textContent = …; circle.bindTooltip(label, …)` (Leaflet accepts an `HTMLElement`), for
  both calls. Keep the `place-name` class and the 🏠 prefix.
- Test (page test, not a browser): the rendered template has no `bindTooltip(` call taking a
  template literal or string concatenation; or, better, a JS-free check that a place named with
  `&lt;` in the fixture reaches the page through `|tojson` only. Decide which is less brittle
  when writing it.
- Optional, to weigh while there: whether `'unsafe-inline'` in `script-src` is still needed (the
  page's script is inline; a hash or nonce would remove it). Measure nothing; just say in the
  commit whether it was kept and why.

No documentation or capture changes expected (same visible tooltips).
