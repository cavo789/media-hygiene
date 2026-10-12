# 0111 — People: names in the `.xmp` sidecars (opt-in) and a column of the inventory

- **Priority**: Low — naming and search work; this carries the names to other tools
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/tags/xmp_doc.py`, `src/media_hygiene/tags/xmp_merge.py`, `src/media_hygiene/tags/xmp_owner.py`, `src/media_hygiene/services/xmp_plan.py`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/index/listing.py`, `src/media_hygiene/report/`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`, `documentation/en/commands/xmp.md`, `documentation/fr/commands/xmp.md`, `documentation/en/reference-inventory.md`, `documentation/fr/reference-inventory.md`

## Context

TODO 0091 names the people (`[[people.person]]`) and `search` finds them; 0095 sorts by person.
The names never leave the tool yet: not in the `.xmp` sidecars that `xmp` writes, not in the
inventory workbook. 0091 left both for after the `person` rule (done since).

Decided in review (2026-10-12): writing the names next to the photos is **opt-in** — the
family's names would land in files that travel with the photos (copied to a phone, a cloud, a
shared drive).

## Goal

- `xmp`: a new source `person` for `[tags] xmp_sources`, **not** in the default list. When
  chosen, the names of the people seen on a photo go into `Iptc4xmpExt:PersonInImage` (the
  field digiKam, Lightroom and Immich read), with the same care as the other fields: a value
  another application wrote is kept, ours is tracked and taken back when the source is removed
  or a face is renamed; `undo` restores the sidecar as before.
- One line when `person` is in `xmp_sources`, before writing: the names are written next to
  the photos, where anyone who gets a copy can read them.
- Inventory (`inventory.xlsx` / `.csv`): a "People" column, the names seen on each photo, from
  the index and `config.toml` alone (no face read again).
- Docs en + fr: `reference-tags.md` (the `xmp` section), `commands/xmp.md`,
  `reference-inventory.md`.

## Acceptance

- Default `xmp_sources`: no name written anywhere (test).
- `person` chosen: `PersonInImage` filled, kept when another tool set it, taken back when
  removed (exiftool check by hand, like 0085).
- The inventory column lists the names; empty without `[[people.person]]`.
