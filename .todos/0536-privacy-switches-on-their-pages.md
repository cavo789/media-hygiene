# 0536 — Privacy switches visible where they act: reverse lookup, GPS in shares

- **Priority**: High
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/places/`, `src/media_hygiene/share/`, `src/media_hygiene/places/toml_edit.py`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

"If this feature is not shown in the web interface, it is as if it did not exist." Each setting
is placed **on the page where it acts**, next to its visible effect (no catch-all settings page),
saved with `places/toml_edit` (comments kept, atomic) and **read back from disk** before being
shown. Follows 0532 (folder roles); analysed in detail at implementation time.

## Wanted

- Places page: `[places] reverse_lookup` (ask / yes / no) as a visible switch, its consequence
  in one sentence (positions sent online or not).
- Share dialog: "keep the position" (`[share] keep_gps`), size (`long_side_px`) and quality
  (`quality`) in the dialog itself, the default saved on request.
- To decide: `[review] lan` / `lan_phone_originals` shown as a state only (network security).
