# 0570 — Faces known by path + content id; renamed photos found after every audit

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/config/photo_ref.py`, `src/media_hygiene/config/people_files.py`, `src/media_hygiene/people/config_file.py`, `src/media_hygiene/people/person_files.py`, `src/media_hygiene/people/followed.py`, `src/media_hygiene/people/known.py`, `src/media_hygiene/services/photo_refs_audit.py`, the `import` service, the home page's audit step, `documentation/en/`, `documentation/fr/`

## Why

The rest of 0551 **une photo connue par son chemin + son identifiant de contenu** (PARTIAL: places
done). Faces in `people/*.toml` are still `<path>#<n>`, lost when a folder is renamed in Explorer.
The maintainer decided on 2026-11-02 that a photo renamed outside the tool must be found again
after `import` and the home page's audit too, not only after `mh audit`.

## What

- Faces as `{path = '…', id = "<16 hex>:<size>", face = n}`, through `config/photo_ref.py`. The old
  `<path>#<n>` form loads and is rewritten at the next save. Atomic save, comments kept, read back.
- An edited photo loses its face names (another photo).
- `photo_refs_audit` (places, then faces) runs at the end of every audit: `mh audit`, `import`'s
  audit and the home page's.
- Tests per event, as in `tests/unit/test_photo_ref.py`: sort, undo, quarantine and back, Explorer
  rename then audit (each of the 3 entry points), copy to another drive, edited copy, identical
  copies (tie broken by name).
- Docs en + fr (`commands/people.md`, `reference-people` if any).
