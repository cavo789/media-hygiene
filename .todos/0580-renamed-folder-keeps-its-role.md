# 0580 — A folder renamed in Explorer: offer to carry its role over

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/folder_role_desk.py`, `src/media_hygiene/search/templates/`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, review of 2026-11-02)

0532 (commit 15e8f5a3) lists a folder with a role that no longer exists as missing, with a
*Remove* button. Decision: when a folder now holds the same content, offer to carry the role
over to it.

## What

- For a missing folder, look for a candidate: a sibling (or a folder of the same drive) whose
  files match the index rows of the old path (same digests), cheaply, from the index only.
- Offer "Carry the role to <new name>" next to *Remove*; the write goes through `toml_edit`,
  read back and shown.
- No candidate: only *Remove*, as today.

## Tests

- Folder renamed (same files): the candidate is found and the role moves; config.toml read back.
- Folder deleted: no candidate.
- Two candidates: none proposed automatically, both listed.
