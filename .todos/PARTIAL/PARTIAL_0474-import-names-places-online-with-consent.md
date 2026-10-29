# 0474 — After an import: name the new photos' places online, with the user's consent

- **Priority**: Low
- **Batch**: slideshow
- **Depends**: 0472
- **Files**: `src/media_hygiene/cli/cmd_import.py`, `src/media_hygiene/geo/nominatim.py`, `src/media_hygiene/places/`, `src/media_hygiene/config/`

## Why

The maintainer, 2026-10-29: `import` now runs `audit` at once; after it, offer to find the
names of buildings and monuments at the new photos' GPS positions, to show them on the TV (0472)
and in `mh places`.

## Design change (to decide)

Today **no position ever leaves the machine** (CLAUDE.md, `geo/`): Nominatim is only asked for
an area by a **typed name**, from `places`. A reverse lookup sends coordinates. What it loses:
the "nothing leaves your PC" promise for this step. Mitigations to keep: an explicit question
each time (default No, `[places] reverse_lookup` to say always/never), positions rounded and
grouped (one request per cluster of the import, not per photo), Nominatim's rules (1 request/s,
User-Agent, `[places] nominatim_url`, empty disables), results cached in the index so a
position is asked once. Alternative without sending anything: the offline landmark list of 0472.

## What

After `import`'s audit, when the new files have GPS clusters not inside a user's place:
« N new places found. Look up their names online (OpenStreetMap)? [y/N] » → reverse lookup per
cluster (`zoom` for buildings, to check), stored as suggestions; `mh places` shows them for
the user to keep as a named place (nothing written to `config.toml` without a click).

## Acceptance

- Answer No / no network / empty URL: no request at all (test with a fake server).
- One request per cluster, cached; a second import of the same place asks nothing.

## Decided (2026-10-29, the maintainer)

Yes, opt-in: positions may leave the machine only after an explicit Yes each time (default No), per cluster, rounded, cached. Update CLAUDE.md's "no position ever leaves the machine" to "never without your consent" and the docs.

## Status — PARTIAL (2026-10-29)

Done: `cli/import_places.py` asks after `import`'s copies (default No; `[places] reverse_lookup`
ask/never/always; `--yes` sends nothing unless `always`; empty `nominatim_url` sends nothing);
`geo/reverse.py` (zoom 18, 1 req/s, User-Agent, positions rounded to 3 decimals, one per spot);
`services/place_names.py` caches the names in `/cache/place-names.json` (asked once); the
slideshow shows them first (0472). Tests with a fake server (`tests/unit/test_import_place_names.py`).
Docs EN+FR (import, slideshow, places), CLAUDE.md geo line.

Remaining:
- `mh places` shows the names found as suggestions, kept as a named place on a click only.
- Videos' positions (the import reads images' EXIF only).
- Run it also after the phone launcher's audit (0451) — fits 0475's chain.
